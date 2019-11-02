"""
Mail merge using CSV database and jinja2 template email.

API implementation.

Andrew DeOrio <awdeorio@umich.edu>
"""
from __future__ import print_function
import os
import io
import sys
import smtplib
import configparser
import getpass

# NOTE: Python 2.x UTF8 support requires csv and email backports
try:
    from backports import csv
except ImportError:
    import csv

import future.backports.email as email
import future.backports.email.mime
import future.backports.email.mime.application
import future.backports.email.mime.multipart
import future.backports.email.mime.text
import future.backports.email.parser
import future.backports.email.utils
import future.backports.email.generator
import markdown
import jinja2
import chardet


# Configuration
TEMPLATE_FILENAME_DEFAULT = "mailmerge_template.txt"
DATABASE_FILENAME_DEFAULT = "mailmerge_database.csv"
CONFIG_FILENAME_DEFAULT = "mailmerge_server.conf"


class MessageTemplate:
    """Represent a templated email message.

    This object combines an email.message object with the template abilities of
    Jinja2's Template object.
    """

    def __init__(self, template_filename):
        """Initialize variables and Jinja2 template."""
        self.template_filename = template_filename
        self.message = None
        self.sender = None
        self.recipients = None
        self.attachments = []

        # Configure Jinja2 template engine
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(template_filename)),
            undefined=jinja2.StrictUndefined,
        )
        self.template = template_env.get_template(
            os.path.basename(template_filename),
        )

    def render(self, context):
        """Return rendered message object."""
        raw_message = self.template.render(**context)
        self.parsemail(raw_message)
        self.convert_markdown()
        self.addattachments()
        return self.sender, self.recipients, self.message

    def parsemail(self, raw_message):
        """Parse message headers, then remove BCC header."""
        self.message = email.parser.Parser().parsestr(raw_message)

        # Detect encoding
        detected = chardet.detect(bytearray(raw_message, "utf-8"))
        encoding = detected["encoding"]
        print(">>> encoding {}".format(encoding))
        for part in self.message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            part.set_charset(encoding)

        # Extract recipients
        addrs = email.utils.getaddresses(self.message.get_all("TO", [])) + \
            email.utils.getaddresses(self.message.get_all("CC", [])) + \
            email.utils.getaddresses(self.message.get_all("BCC", []))
        self.recipients = [x[1] for x in addrs]
        self.message.__delitem__("bcc")
        self.message.__setitem__('Date', email.utils.formatdate())
        self.sender = self.message["from"]

    def _create_boundary(self):
        """Add boundary parameter to multipart message if not present."""
        if not self.message.is_multipart():
            return
        if self.message.get_boundary() is not None:
            return

        # HACK: Python2 lists do not natively have a `copy`
        # method. Unfortunately, due to a bug in the Backport for the email
        # module, the method `Message.set_boundary` converts the Message
        # headers into a native list, so that other methods that rely on
        # "copying" the Message headers fail.  `Message.set_boundary` is called
        # from `Generator.handle_multipart` if the message does not already
        # have a boundary present. (This method itself is called from
        # `Message.as_string`.)  Hence, to prevent `Message.set_boundary` from
        # being called, add a boundary header manually.
        # pylint: disable=protected-access
        boundary = email.generator.Generator._make_boundary(
            self.message.policy.linesep)
        self.message.set_param('boundary', boundary)

    def make_message_multipart(self):
        """Convert a message into a multipart message."""
        if not self.message.is_multipart():
            multipart_message = email.mime.multipart.MIMEMultipart(
                'alternative')
            for header_key in set(self.message.keys()):
                # Preserve duplicate headers
                values = self.message.get_all(header_key, failobj=[])
                for value in values:
                    multipart_message[header_key] = value
            original_text = self.message.get_payload()
            multipart_message.attach(email.mime.text.MIMEText(original_text))
            self.message = multipart_message
        # HACK: For Python2 (see comments in `_create_boundary`)
        self._create_boundary()

    def convert_markdown(self):
        """Convert markdown in message text to HTML."""
        if not self.message['Content-Type'].startswith("text/markdown"):
            return

        del self.message['Content-Type']
        # Convert the text from markdown and then make the message multipart
        self.make_message_multipart()
        for payload_item in set(self.message.get_payload()):
            # Assume the plaintext item is formatted with markdown.
            # Add corresponding HTML version of the item as the last part of
            # the multipart message (as per RFC 2046)
            if payload_item['Content-Type'].startswith('text/plain'):
                original_text = payload_item.get_payload()
                html_text = markdown.markdown(original_text)
                html_payload = future.backports.email.mime.text.MIMEText(
                    "<html><body>{}</body></html>".format(html_text),
                    "html",
                )
                self.message.attach(html_payload)

    def addattachments(self):
        """Add the attachments from the message headers."""
        if 'attachment' not in self.message:
            return

        self.make_message_multipart()

        attachment_filepaths = self.message.get_all('attachment', failobj=[])
        template_parent_dir = os.path.dirname(self.template_filename)

        for attachment_filepath in attachment_filepaths:
            attachment_filepath = attachment_filepath.strip()
            attachment_filepath = os.path.expanduser(attachment_filepath)
            if not attachment_filepath:
                continue
            if not os.path.isabs(attachment_filepath):
                # Relative paths are relative to the template's parent dir
                attachment_filepath = os.path.join(template_parent_dir,
                                                   attachment_filepath)
            normalized_path = os.path.abspath(attachment_filepath)
            self.attachments.append(normalized_path)

            # Check that the attachment exists
            if not os.path.exists(normalized_path):
                print("Error: can't find attachment " + normalized_path)
                sys.exit(1)  # FIXME

            filename = os.path.basename(normalized_path)
            with open(normalized_path, "rb") as attachment:
                part = email.mime.application.MIMEApplication(
                    attachment.read(),
                    Name=filename,
                )
            part.add_header('Content-Disposition',
                            'attachment; filename="{}"'.format(filename))
            self.message.attach(part)
            print(">>> attached {}".format(normalized_path))

        del self.message['attachment']


class SendmailClient:
    """Represent a client connection to an SMTP server."""

    def __init__(self, config_filename):
        """Read configuration from config_filename."""
        config = configparser.RawConfigParser()
        config.read(config_filename)
        self.host = config.get("smtp_server", "host")
        self.port = config.getint("smtp_server", "port")
        self.security = config.get("smtp_server", "security")

        if self.security != "Never":
            self.username = config.get("smtp_server", "username")
            prompt = ">>> password for {} on {}: ".format(
                self.username, self.host)
            self.password = getpass.getpass(prompt)

    def sendmail(self, sender, recipients, message):
        """Send email message."""
        if self.security == "SSL/TLS":
            smtp = smtplib.SMTP_SSL(self.host, self.port)
        elif self.security == "STARTTLS":
            smtp = smtplib.SMTP(self.host, self.port)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
        elif self.security == "Never":
            smtp = smtplib.SMTP(self.host, self.port)
        else:
            raise configparser.Error("Unrecognized security type: {}".format(
                self.security))

        # Send credentials
        if self.security != "Never":
            assert self.username
            assert self.password
            smtp.login(self.username, self.password)

        # Send message.  Note that we can't use the elegant
        # "smtp.send_message(message)" because that's python3 only
        smtp.sendmail(sender, recipients, message.as_string())
        smtp.close()


def read_csv_database(database_path):
    """Read database CSV file, providing one line at a time."""
    with io.open(database_path, "r") as database_file:
        reader = csv.DictReader(database_file)
        for row in reader:
            yield row


def main(database_path, template_path, config_path, limit, dry_run):
    """Read files and render templates."""
    # Read template
    message_template = MessageTemplate(template_path)

    # Read CSV file database
    csv_database = read_csv_database(database_path)

    # Read SMTP client configuration
    sendmail_client = SendmailClient(config_path)

    # Each row corresponds to one email message
    for i, row in enumerate(csv_database):
        if limit >= 0 and i >= limit:
            # limit == -1 for no limit
            break

        sender, recipients, message = message_template.render(row)
        yield
        print(">>> message {}".format(i))  # FIXME
        print(message.as_string())

        # Send message
        if not dry_run:
            sendmail_client.sendmail(sender, recipients, message)
            print(">>> sent message {}".format(i))  # FIXME

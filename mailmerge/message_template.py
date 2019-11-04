"""Represent a templated email message."""

from __future__ import print_function
import os
import sys
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


class MessageTemplate(object):
    """Represent a templated email message.

    This object combines an email.message object with the template abilities of
    Jinja2's Template object.
    """

    # We need to inherit from object for Python 2 compantibility
    # https://python-future.org/compatible_idioms.html#custom-class-behaviour
    # pylint: disable=bad-option-value,useless-object-inheritance

    def __init__(self, template_path):
        """Initialize variables and Jinja2 template."""
        self.template_path = template_path
        self.message = None
        self.sender = None
        self.recipients = None
        self.attachments = []

        # Configure Jinja2 template engine
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(template_path)),
            undefined=jinja2.StrictUndefined,
        )
        self.template = template_env.get_template(
            os.path.basename(template_path),
        )

    def render(self, context):
        """Return rendered message object."""
        raw_message = self.template.render(context)
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
        template_parent_dir = os.path.dirname(self.template_path)

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
                sys.exit(1)

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

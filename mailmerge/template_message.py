"""
Represent a templated email message.

Andrew DeOrio <awdeorio@umich.edu>
"""

import future.backports.email as email
import future.backports.email.mime
import future.backports.email.mime.application
import future.backports.email.mime.multipart
import future.backports.email.mime.text
import future.backports.email.parser
import future.backports.email.utils
import markdown
import jinja2
from .exceptions import MailmergeError

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path


class TemplateMessage(object):
    """Represent a templated email message.

    This object combines an email.message object with the template abilities of
    Jinja2's Template object.
    """

    # The external interface to this class is pretty simple.  We don't need
    # more than one public method.
    # pylint: disable=too-few-public-methods
    #
    # We need to inherit from object for Python 2 compantibility
    # https://python-future.org/compatible_idioms.html#custom-class-behaviour
    # pylint: disable=bad-option-value,useless-object-inheritance

    def __init__(self, template_path):
        """Initialize variables and Jinja2 template."""
        self.template_path = Path(template_path)
        self._message = None
        self._sender = None
        self._recipients = None

        # Configure Jinja2 template engine with the template dirname as root.
        #
        # Note: jinja2's FileSystemLoader does not support pathlib Path objects
        # in Python 2. https://github.com/pallets/jinja/pull/1064
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path.parent)),
            undefined=jinja2.StrictUndefined,
        )
        self.template = template_env.get_template(
            template_path.parts[-1],  # basename
        )

    def render(self, context):
        """Return rendered message object."""
        try:
            raw_message = self.template.render(context)
        except jinja2.exceptions.TemplateError as err:
            raise MailmergeError(
                "{}: {}".format(self.template_path, err)
            )
        self._message = email.message_from_string(raw_message)
        self._transform_encoding(raw_message)
        self._transform_recipients()
        self._transform_markdown()
        self._transform_attachments()
        self._message.__setitem__('Date', email.utils.formatdate())
        assert self._sender
        assert self._recipients
        assert self._message
        return self._sender, self._recipients, self._message

    def _transform_encoding(self, raw_message):
        """Detect and set character encoding."""
        encoding = "us-ascii" if is_ascii(raw_message) else "utf-8"
        for part in self._message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            part.set_charset(encoding)

    def _transform_recipients(self):
        """Extract sender and recipients from FROM, TO, CC and BCC fields."""
        # Extract recipients
        addrs = email.utils.getaddresses(self._message.get_all("TO", [])) + \
            email.utils.getaddresses(self._message.get_all("CC", [])) + \
            email.utils.getaddresses(self._message.get_all("BCC", []))
        self._recipients = [x[1] for x in addrs]
        self._message.__delitem__("bcc")
        self._sender = self._message["from"]

    def _make_message_multipart(self):
        """Convert a message into a multipart message."""
        # Do nothing if message already multipart
        if self._message.is_multipart():
            return

        # Create empty multipart message
        multipart_message = email.mime.multipart.MIMEMultipart('alternative')

        # Copy headers.  Avoid duplicate Content-Type and MIME-Version headers,
        # which we set explicitely.  MIME-Version was set when we created an
        # empty mulitpart message.  Content-Type will be set when we copy the
        # original text later.
        for header_key in set(self._message.keys()):
            if header_key.lower() in ["content-type", "mime-version"]:
                continue
            values = self._message.get_all(header_key, failobj=[])
            for value in values:
                multipart_message[header_key] = value

        # Copy text, preserving original encoding
        original_text = self._message.get_payload(decode=True)
        original_subtype = self._message.get_content_subtype()
        original_encoding = str(self._message.get_charset())
        multipart_message.attach(email.mime.text.MIMEText(
            original_text,
            _subtype=original_subtype,
            _charset=original_encoding,
        ))

        # Replace original message with multipart message
        self._message = multipart_message

    def _transform_markdown(self):
        """Convert markdown in message text to HTML."""
        # Do nothing if Content-Type is not text/markdown
        if not self._message['Content-Type'].startswith("text/markdown"):
            return

        # Remove the markdown Content-Type header, it's non-standard for email
        del self._message['Content-Type']

        # Make sure the message is multipart.  We need a multipart message so
        # that we can add an HTML part containing rendered Markdown.
        self._make_message_multipart()

        # Extract unrendered text and encoding.  We assume that the first
        # plaintext payload is formatted with Markdown.
        for mimetext in self._message.get_payload():
            if mimetext['Content-Type'].startswith('text/plain'):
                encoding = str(mimetext.get_charset())
                text = mimetext.get_payload(decode=True).decode(encoding)
                break
        assert encoding
        assert text

        # Render Markdown to HTML and add the HTML as the last part of the
        # multipart message as per RFC 2046.
        #
        # Note: We need to use u"..." to ensure that unicode string
        # substitution works properly in Python 2.
        #
        # https://docs.python.org/3/library/email.mime.html#email.mime.text.MIMEText
        html = markdown.markdown(text)
        payload = future.backports.email.mime.text.MIMEText(
            u"<html><body>{}</body></html>".format(html),
            _subtype="html",
            _charset=encoding,
        )
        self._message.attach(payload)

    def _transform_attachments(self):
        """Parse Attachment headers and add attachments."""
        # Do nothing if message has no attachment header
        if 'attachment' not in self._message:
            return

        # Make sure the message is multipart.  We need a multipart message in
        # order to add an attachment.
        self._make_message_multipart()

        # Add each attachment to the message
        for path in self._message.get_all('attachment', failobj=[]):
            path = self._resolve_attachment_path(path)
            with path.open("rb") as attachment:
                content = attachment.read()
            basename = path.parts[-1]
            part = email.mime.application.MIMEApplication(
                content,
                Name=str(basename),
            )
            part.add_header(
                'Content-Disposition',
                'attachment; filename="{}"'.format(basename),
            )
            self._message.attach(part)

        # Remove the attachment header, it's non-standard for email
        del self._message['attachment']

    def _resolve_attachment_path(self, path):
        """Find attachment file or raise MailmergeError."""
        # Error on empty path
        if not path.strip():
            raise MailmergeError("Empty attachment header.")

        # Create a Path object and handle home directory (tilde ~) notation
        path = Path(path.strip())
        path = path.expanduser()

        # Relative paths are relative to the template's parent dir
        if not path.is_absolute():
            path = self.template_path.parent/path

        # Resolve any symlinks
        path = path.resolve()

        # Check that the attachment exists
        if not path.exists():
            raise MailmergeError("Attachment not found: {}".format(path))

        return path


def is_ascii(string):
    """Return True is string contains only is us-ascii encoded characters."""
    def is_ascii_char(char):
        return 0 <= ord(char) <= 127
    return all(is_ascii_char(char) for char in string)

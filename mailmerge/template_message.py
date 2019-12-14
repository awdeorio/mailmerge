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
import future.backports.email.generator
import markdown
import jinja2
import chardet
from . import utils

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
        raw_message = self.template.render(context)
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
        self._message = email.parser.Parser().parsestr(raw_message)
        detected = chardet.detect(bytearray(raw_message, "utf-8"))
        encoding = detected["encoding"]
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
        if not self._message.is_multipart():
            multipart_message = email.mime.multipart.MIMEMultipart(
                'alternative')
            for header_key in set(self._message.keys()):
                # Preserve duplicate headers
                values = self._message.get_all(header_key, failobj=[])
                for value in values:
                    multipart_message[header_key] = value
            original_text = self._message.get_payload()
            multipart_message.attach(email.mime.text.MIMEText(original_text))
            self._message = multipart_message

    def _transform_markdown(self):
        """Convert markdown in message text to HTML."""
        if not self._message['Content-Type'].startswith("text/markdown"):
            return

        del self._message['Content-Type']
        # Convert the text from markdown and then make the message multipart
        self._make_message_multipart()
        for payload_item in set(self._message.get_payload()):
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
                self._message.attach(html_payload)

    def _transform_attachments(self):
        """Parse Attachment headers and add attachments."""
        if 'attachment' not in self._message:
            return

        self._make_message_multipart()

        attachment_filepaths = self._message.get_all('attachment', failobj=[])

        for attachment_filepath in attachment_filepaths:
            normalized_path = self._resolve_attachment_path(attachment_filepath)
            with normalized_path.open("rb") as attachment:
                attachment_content = attachment.read()
            basename = normalized_path.parts[-1]
            part = email.mime.application.MIMEApplication(
                attachment_content,
                Name=str(basename),
            )
            part.add_header('Content-Disposition',
                            'attachment; filename="{}"'.format(basename))
            self._message.attach(part)

        del self._message['attachment']

    def _resolve_attachment_path(self, path):
        """Find a file specified by an attachment header.

        Raise MailmergeError on failure.
        """
        template_parent_dir = self.template_path.parent
        path = path.strip()
        if not path:
            raise utils.MailmergeError("Empty attachment header.")

        path = Path(path)
        path = path.expanduser()

        if not path.is_absolute():
            # Relative paths are relative to the template's parent dir
            path = template_parent_dir/path
        normalized_path = path.resolve()

        # Check that the attachment exists
        if not normalized_path.exists():
            raise utils.MailmergeError(
                "Attachment not found: {}".format(normalized_path)
            )

        return normalized_path

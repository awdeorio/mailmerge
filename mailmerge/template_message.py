"""
Represent a templated email message.

Andrew DeOrio <awdeorio@umich.edu>
"""

import re
from pathlib import Path
from xml.etree import ElementTree
import email
import email.mime
import email.mime.application
import email.mime.multipart
import email.mime.text
import html5lib
import markdown
import jinja2
from . import exceptions


class TemplateMessage:
    """Represent a templated email message.

    This object combines an email.message object with the template abilities of
    Jinja2's Template object.
    """

    # The external interface to this class is pretty simple.  We don't need
    # more than one public method.
    # pylint: disable=too-few-public-methods

    def __init__(self, template_path):
        """Initialize variables and Jinja2 template."""
        self.template_path = Path(template_path)
        self._message = None
        self._sender = None
        self._recipients = None
        self._attachment_content_ids = {}

        # Configure Jinja2 template engine with the template dirname as root.
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path.parent),
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
            raise exceptions.MailmergeError(f"{self.template_path}: {err}")
        self._message = email.message_from_string(raw_message)
        self._transform_encoding(raw_message)
        self._transform_recipients()
        self._transform_markdown()
        self._transform_attachments()
        self._transform_attachment_references()
        self._message.add_header('Date', email.utils.formatdate())
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
        # The docs recommend using __delitem__()
        # https://docs.python.org/3/library/email.message.html#email.message.EmailMessage.__delitem__
        # pylint: disable=unnecessary-dunder-call
        addrs = email.utils.getaddresses(self._message.get_all("TO", [])) + \
            email.utils.getaddresses(self._message.get_all("CC", [])) + \
            email.utils.getaddresses(self._message.get_all("BCC", []))
        self._recipients = [x[1] for x in addrs]
        self._message.__delitem__("bcc")
        self._sender = self._message["from"]

    def _make_message_multipart(self):
        """
        Convert self._message into a multipart message.

        Specifically, if the message's content-type is not multipart, this
        method will create a new `multipart/related` message, copy message
        headers and re-attach the original payload.
        """
        # Do nothing if message already multipart
        if self._message.is_multipart():
            return

        # Create empty multipart message
        multipart_message = email.mime.multipart.MIMEMultipart('related')

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
        """
        Convert markdown in message text to HTML.

        Specifically, if the message's content-type is `text/markdown`, we
        transform `self._message` to have the following structure:

        multipart/related
         └── multipart/alternative
             ├── text/plain (original markdown plaintext)
             └── text/html (converted markdown)

        Attachments should be added as subsequent payload items of the
        top-level `multipart/related` message.
        """
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
                original_text_payload = mimetext
                encoding = str(mimetext.get_charset())
                text = mimetext.get_payload(decode=True).decode(encoding)
                break
        assert original_text_payload
        assert encoding
        assert text
        # Remove the original text payload.
        self._message.set_payload(
            self._message.get_payload().remove(original_text_payload))

        # Add a multipart/alternative part to the message. Email clients can
        # choose which payload-part they wish to render.
        #
        # Render Markdown to HTML and add the HTML as the last part of the
        # multipart/alternative message as per RFC 2046.
        #
        # https://docs.python.org/3/library/email.mime.html#email.mime.text.MIMEText
        html = markdown.markdown(text, extensions=['nl2br'])
        html_payload = email.mime.text.MIMEText(
            f"<html><body>{html}</body></html>",
            _subtype="html",
            _charset=encoding,
        )

        message_payload = email.mime.multipart.MIMEMultipart('alternative')
        message_payload.attach(original_text_payload)
        message_payload.attach(html_payload)

        self._message.attach(message_payload)

    def _transform_attachments(self):
        """
        Parse attachment headers and generate content-id headers for each.

        Attachments are added to the payload of a `multipart/related` message.
        For instance, a plaintext message with attachments would have the
        following structure:

        multipart/related
         ├── text/plain
         ├── attachment1
         └── attachment2

        Another example: If the original message contained `text/markdown`,
        then the message would have the following structure after transforming
        markdown and attachments:

        multipart/related
         ├── multipart/alternative
         │   ├── text/plain
         │   └── text/html
         ├── attachment1
         └── attachment2
        """
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
                f'attachment; filename="{basename}"'
            )

            # When processing inline images in the email body, we will
            # reference the Content-ID for an attachment with the same path
            # using 'cid:[content-id]'.
            cid, cid_header_value = make_attachment_content_id()
            self._attachment_content_ids[str(path)] = cid
            part.add_header('Content-Id', cid_header_value)

            self._message.attach(part)

        # Remove the attachment header, it's non-standard for email
        del self._message['attachment']

    def _transform_attachment_references(self):
        """
        Replace references to inline-images in the email body's HTML content.

        Specifically, match inline-image src attributes with content-ids from
        image attachments, if available.
        """
        if not self._message.is_multipart():
            return

        for part in self._message.walk():
            if not part['Content-Type'].startswith('text/html'):
                continue

            html = part.get_payload(decode=True).decode('utf-8')
            document = html5lib.parse(html, namespaceHTMLElements=False)
            images = document.findall('.//img')
            if len(images) == 0:
                continue

            for img in document.findall('.//img'):
                src = img.get('src')
                try:
                    src = str(self._resolve_attachment_path(src))
                except exceptions.MailmergeError:
                    # The src is not a valid filesystem path, so it could not
                    # have been attached to the email.
                    continue

                if src in self._attachment_content_ids:
                    cid = self._attachment_content_ids[src]
                    url = f"cid:{cid}"
                    img.set('src', url)
                    # Only clear the header if we are transforming an
                    # attachment reference. See comment below for context.
                    del part['Content-Transfer-Encoding']

            # Unless the _charset argument is explicitly set to None, the
            # MIMEText object created will have both a Content-Type header with
            # a charset parameter, and a Content-Transfer-Encoding header.
            # This means that a subsequent set_payload call will not result in
            # an encoded payload, even if a charset is passed in the
            # set_payload() command.
            # We “reset” this behavior by deleting the
            # Content-Transfer-Encoding header, after which a set_payload()
            # call automatically encodes the new payload (and adds a new
            # Content-Transfer-Encoding header).
            #
            # We only need to update the message if we cleared the header,
            # which only happens if we transformed an attachment reference.
            if 'Content-Transfer-Encoding' not in part:
                new_html = ElementTree.tostring(document).decode('utf-8')
                part.set_payload(new_html)

    def _resolve_attachment_path(self, path):
        """Find attachment file or raise MailmergeError."""
        # Error on empty path
        if not path.strip():
            raise exceptions.MailmergeError("Empty attachment header.")

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
            raise exceptions.MailmergeError(f"Attachment not found: {path}")

        return path


def is_ascii(string):
    """Return True is string contains only is us-ascii encoded characters."""
    def is_ascii_char(char):
        return 0 <= ord(char) <= 127
    return all(is_ascii_char(char) for char in string)


def make_attachment_content_id():
    """
    Return an RFC 2822 compliant Message-ID and corresponding header.

    For instance: `20020201195627.33539.96671@mailmerge.invalid`
    """
    # Using domain '.invalid' to prevent leaking the hostname. The TLD is
    # reserved, see: https://en.wikipedia.org/wiki/.invalid
    cid_header = email.utils.make_msgid(domain="mailmerge.invalid")
    # The cid_header is of format `<cid>`. We need to extract the cid for
    # later lookup.
    cid = re.search('<(.*)>', cid_header).group(1)
    return cid, cid_header

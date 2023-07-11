"""
Tests for TemplateMessage.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
import re
import shutil
import textwrap
import collections
from pathlib import Path
import pytest
import markdown
import html5lib
from mailmerge import TemplateMessage, MailmergeError
from . import utils


def test_simple(tmp_path):
    """Render a simple template."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hello {{name}}!
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "name": "world",
    })
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]
    plaintext = message.get_payload()
    assert "Hello world!" in plaintext


def test_no_substitutions(tmp_path):
    """Render a template with an empty context."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hello world!
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({})
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]
    plaintext = message.get_payload()
    assert "Hello world!" in plaintext


def test_multiple_substitutions(tmp_path):
    """Render a template with multiple context variables."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: from@test.com

        Hi, {{name}},

        Your number is {{number}}.
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "email": "myself@mydomain.com",
        "name": "Myself",
        "number": 17,
    })
    assert sender == "from@test.com"
    assert recipients == ["myself@mydomain.com"]
    plaintext = message.get_payload()
    assert "Hi, Myself," in plaintext
    assert "Your number is 17" in plaintext


def test_bad_jinja(tmp_path):
    """Bad jinja template should produce an error."""
    template_path = tmp_path / "template.txt"
    template_path.write_text("TO: {{error_not_in_database}}")
    template_message = TemplateMessage(template_path)
    with pytest.raises(MailmergeError):
        template_message.render({"name": "Bob", "number": 17})


def test_cc_bcc(tmp_path):
    """CC recipients should receive a copy."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>
        CC: My Colleague <mycolleague@mydomain.com>
        BCC: Secret <secret@mydomain.com>

        Hello world
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "email": "myself@mydomain.com",
    })

    # Verify recipients include CC and BCC
    assert sender == "My Self <myself@mydomain.com>"
    assert recipients == [
        "myself@mydomain.com",
        "mycolleague@mydomain.com",
        "secret@mydomain.com",
    ]

    # Make sure BCC recipients are *not* in the message
    plaintext = message.get_payload()
    assert "BCC" not in plaintext
    assert "secret@mydomain.com" not in plaintext
    assert "Secret" not in plaintext


def stripped_strings_equal(s_1, s_2):
    """Compare strings ignoring trailing whitespace."""
    s_1 = s_1.strip() if s_1 else ''
    s_2 = s_2.strip() if s_2 else ''
    return s_1 == s_2


def html_docs_equal(e_1, e_2):
    """Return true if two HTML trees are equivalent."""
    # Based on: https://stackoverflow.com/a/24349916
    if not stripped_strings_equal(e_1.tag, e_2.tag):
        return False
    if not stripped_strings_equal(e_1.text, e_2.text):
        return False
    if not stripped_strings_equal(e_1.tail, e_2.tail):
        return False
    if e_1.attrib != e_2.attrib:
        return False
    if len(e_1) != len(e_2):
        return False
    return all(html_docs_equal(c_1, c_2) for c_1, c_2 in zip(e_1, e_2))


def test_html(tmp_path):
    """Verify HTML template results in a simple rendered message."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com
        Content-Type: text/html

        <html>
          <body>
            <p>{{message}}</p>
          </body>
        </html>
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "message": "Hello world"
    })

    # Verify sender and recipients
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]

    # A simple HTML message is not multipart
    assert not message.is_multipart()

    # Verify encoding
    assert message.get_charset() == "us-ascii"
    assert message.get_content_charset() == "us-ascii"
    assert message.get_content_type() == "text/html"

    # Verify content
    htmltext = html5lib.parse(message.get_payload())
    expected = html5lib.parse("<html><body><p>Hello world</p></body></html>")
    assert html_docs_equal(htmltext, expected)


def test_html_plaintext(tmp_path):
    """Verify HTML and plaintest multipart template."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"

        This is a MIME-encoded message. If you are seeing this, your mail
        reader is old.

        --boundary
        Content-Type: text/plain; charset=us-ascii

        {{message}}

        --boundary
        Content-Type: text/html; charset=us-ascii

        <html>
          <body>
            <p>{{message}}</p>
          </body>
        </html>
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "message": "Hello world"
    })

    # Verify sender and recipients
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]

    # Should be multipart: plaintext and HTML
    assert message.is_multipart()
    parts = message.get_payload()
    assert len(parts) == 2
    plaintext_part, html_part = parts

    # Verify plaintext part
    assert plaintext_part.get_charset() == "us-ascii"
    assert plaintext_part.get_content_charset() == "us-ascii"
    assert plaintext_part.get_content_type() == "text/plain"
    plaintext = plaintext_part.get_payload()
    plaintext = plaintext.strip()
    assert plaintext == "Hello world"

    # Verify html part
    assert html_part.get_charset() == "us-ascii"
    assert html_part.get_content_charset() == "us-ascii"
    assert html_part.get_content_type() == "text/html"
    htmltext = html5lib.parse(html_part.get_payload())
    expected = html5lib.parse("<html><body><p>Hello world</p></body></html>")
    assert html_docs_equal(htmltext, expected)


def extract_text_from_markdown_payload(plaintext_part, mime_type):
    """Decode text from the given message part."""
    assert plaintext_part['Content-Type'].startswith(mime_type)
    plaintext_encoding = str(plaintext_part.get_charset())
    plaintext = plaintext_part.get_payload(decode=True) \
                              .decode(plaintext_encoding)
    return plaintext


def test_markdown(tmp_path):
    """Markdown messages should be converted to HTML."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: Bob <bob@bobdomain.com>
        CONTENT-TYPE: text/markdown

        Hi, **{{name}}**,

        You can add:

        - Emphasis, aka italics, with *asterisks* or _underscores_.
        - Strong emphasis, aka bold, with **asterisks** or __underscores__.
        - Combined emphasis with **asterisks and _underscores_**.
        - Strikethrough uses two tildes. ~~Scratch this.~~
        - Unordered lists like this one.
        - Ordered lists with numbers:
            1. Item 1
            2. Item 2
        - Preformatted text with `backticks`.

        ---

        # This is a heading.
        ## And another heading.
        How about some [hyperlinks](http://bit.ly/eecs485-wn19-p6)?

        Or code blocks?

        ```
        print("Hello world.")
        ```

        Here's an image not attached with the email:
        ![python logo not attached](
            http://pluspng.com/img-png/python-logo-png-open-2000.png)
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "email": "myself@mydomain.com",
        "name": "Myself",
        "number": 17,
    })

    # Verify sender and recipients
    assert sender == "Bob <bob@bobdomain.com>"
    assert recipients == ["myself@mydomain.com"]

    # Verify message is multipart
    assert message.is_multipart()
    assert message.get_content_subtype() == "related"

    # Make sure there is a single multipart/alternative payload
    assert len(message.get_payload()) == 1
    assert message.get_payload()[0].is_multipart()
    assert message.get_payload()[0].get_content_subtype() == "alternative"

    # And there should be a plaintext part and an HTML part
    message_payload = message.get_payload()[0].get_payload()
    assert len(message_payload) == 2

    # Ensure that the first part is plaintext and the last part
    # is HTML (as per RFC 2046)
    plaintext = extract_text_from_markdown_payload(message_payload[0],
                                                   'text/plain')
    htmltext = extract_text_from_markdown_payload(message_payload[1],
                                                  'text/html')

    # Verify rendered Markdown
    rendered = markdown.markdown(plaintext, extensions=['nl2br'])
    expected = html5lib.parse(rendered)

    htmltext_document = html5lib.parse(htmltext)
    assert html_docs_equal(htmltext_document, expected)


def test_markdown_encoding(tmp_path):
    """Verify encoding is preserved when rendering a Markdown template.

    See Issue #59 for a detailed explanation
    https://github.com/awdeorio/mailmerge/issues/59
    """
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: test@example.com
        CONTENT-TYPE: text/markdown

        Hi, {{name}},
        æøå
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({
        "email": "myself@mydomain.com",
        "name": "Myself",
    })

    # Message should contain an unrendered Markdown plaintext part and a
    # rendered Markdown HTML part
    plaintext_part, html_part = message.get_payload()[0].get_payload()

    # Verify encodings
    assert str(plaintext_part.get_charset()) == "utf-8"
    assert str(html_part.get_charset()) == "utf-8"
    assert plaintext_part["Content-Transfer-Encoding"] == "base64"
    assert html_part["Content-Transfer-Encoding"] == "base64"

    # Verify content, which is base64 encoded
    plaintext = plaintext_part.get_payload(decode=True).decode("utf-8")
    htmltext = html_part.get_payload(decode=True).decode("utf-8")
    assert plaintext == "Hi, Myself,\næøå"
    assert html_docs_equal(
        html5lib.parse(htmltext),
        html5lib.parse(
            "<html><body><p>Hi, Myself,<br />\næøå</p></body></html>"
        )
    )


Attachment = collections.namedtuple(
    "Attachment",
    ["filename", "content", "content_id"],
)


def extract_attachments(message):
    """Return a list of attachments as (filename, content) named tuples."""
    attachments = []
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_content_maintype() == "text":
            continue
        if part.get("Content-Disposition") == "inline":
            continue
        if part.get("Content-Disposition") is None:
            continue
        if part['content-type'].startswith('application/octet-stream'):
            attachments.append(Attachment(
                filename=part.get_param('name'),
                content=part.get_payload(decode=True),
                content_id=part.get("Content-Id")
            ))
    return attachments


def test_attachment_simple(tmpdir):
    """Verify a simple attachment."""
    # Simple attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: attachment.txt

        Hello world
    """), encoding="utf8")

    # Render in tmpdir
    with tmpdir.as_cwd():
        template_message = TemplateMessage(template_path)
        sender, recipients, message = template_message.render({})

    # Verify sender and recipients
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]

    # Verify message is multipart and contains attachment
    assert message.is_multipart()
    attachments = extract_attachments(message)
    assert len(attachments) == 1

    # Verify attachment
    filename, content, _ = attachments[0]
    assert filename == "attachment.txt"
    assert content == b"Hello world\n"


def test_attachment_relative(tmpdir):
    """Attachment with a relative file path is relative to template dir."""
    # Simple attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: attachment.txt

        Hello world
    """), encoding="utf8")

    # Render
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({})

    # Verify directory used to render is different from template directory
    assert os.getcwd() != tmpdir

    # Verify attachment
    attachments = extract_attachments(message)
    filename, content, _ = attachments[0]
    assert filename == "attachment.txt"
    assert content == b"Hello world\n"


def test_attachment_absolute(tmpdir):
    """Attachment with absolute file path."""
    # Simple attachment lives in sub directory
    attachments_dir = tmpdir.mkdir("attachments")
    attachment_path = Path(attachments_dir/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(f"""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: {attachment_path}

        Hello world
    """), encoding="utf8")

    # Render in tmpdir
    with tmpdir.as_cwd():
        template_message = TemplateMessage(template_path)
        _, _, message = template_message.render({})

    # Verify attachment
    attachments = extract_attachments(message)
    filename, content, _ = attachments[0]
    assert filename == "attachment.txt"
    assert content == b"Hello world\n"


def test_attachment_template(tmpdir):
    """Attachment with template as part of file path."""
    # Simple attachment lives in sub directory
    attachments_dir = tmpdir.mkdir("attachments")
    attachment_path = Path(attachments_dir/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: {{filename}}

        Hello world
    """), encoding="utf8")

    # Render in tmpdir
    with tmpdir.as_cwd():
        template_message = TemplateMessage(template_path)
        _, _, message = template_message.render({
            "filename": str(attachment_path),
        })

    # Verify attachment
    attachments = extract_attachments(message)
    filename, content, _ = attachments[0]
    assert filename == "attachment.txt"
    assert content == b"Hello world\n"


def test_attachment_not_found(tmpdir):
    """Attachment file not found."""
    # Template specifying an attachment that doesn't exist
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: attachment.txt

        Hello world
    """), encoding="utf8")

    # Render in tmpdir, which lacks attachment.txt
    template_message = TemplateMessage(template_path)
    with pytest.raises(MailmergeError):
        with tmpdir.as_cwd():
            template_message.render({})


def test_attachment_blank(tmpdir):
    """Attachment header without a filename is an error."""
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT:

        Hello world
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    with pytest.raises(MailmergeError) as err:
        with tmpdir.as_cwd():
            template_message.render({})
    assert "Empty attachment header" in str(err)


def test_attachment_tilde_path(tmpdir):
    """Attachment with home directory tilde notation file path."""
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: ~/attachment.txt

        Hello world
    """), encoding="utf8")

    # Render will throw an error because we didn't create a file in the
    # user's home directory.  We'll just check the filename.
    template_message = TemplateMessage(template_path)
    with pytest.raises(MailmergeError) as err:
        template_message.render({})
    correct_path = Path.home() / "attachment.txt"
    assert str(correct_path) in str(err)


def test_attachment_multiple(tmp_path):
    """Verify multiple attachments."""
    # Copy attachments to tmp dir
    shutil.copy(str(utils.TESTDATA/"attachment_1.txt"), str(tmp_path))
    shutil.copy(str(utils.TESTDATA/"attachment_2.pdf"), str(tmp_path))
    shutil.copy(str(utils.TESTDATA/"attachment_17.txt"), str(tmp_path))

    # Create template .txt file
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>
        ATTACHMENT: attachment_1.txt
        ATTACHMENT: attachment_2.pdf
        ATTACHMENT: attachment_{{number}}.txt

        Hi, {{name}},

        Your number is {{number}}.
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "email": "myself@mydomain.com",
        "name": "Myself",
        "number": 17,
    })

    # Verify sender and recipients
    assert sender == "My Self <myself@mydomain.com>"
    assert recipients == ["myself@mydomain.com"]

    # Verify message is multipart
    assert message.is_multipart()

    # Make sure the attachments are all present and valid
    email_body_present = False
    expected_attachments = {
        "attachment_1.txt": False,
        "attachment_2.pdf": False,
        "attachment_17.txt": False,
    }
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part['content-type'].startswith('text/plain'):
            # This is the email body
            email_body = part.get_payload()
            assert email_body.rstrip() == 'Hi, Myself,\n\nYour number is 17.'
            email_body_present = True
        elif part['content-type'].startswith('application/octet-stream'):
            # This is an attachment
            filename = part.get_param('name')
            file_contents = part.get_payload(decode=True)
            assert filename in expected_attachments
            assert not expected_attachments[filename]
            with (utils.TESTDATA/filename).open('rb') as expected_attachment:
                correct_file_contents = expected_attachment.read()
            assert file_contents == correct_file_contents
            expected_attachments[filename] = True
    assert email_body_present
    assert False not in expected_attachments.values()


def test_attachment_empty(tmp_path):
    """Err on empty attachment field."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com
        ATTACHMENT:

        Hello world
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    with pytest.raises(MailmergeError):
        template_message.render({})


def test_contenttype_attachment_html_body(tmpdir):
    """Content-type is preserved in HTML body."""
    # Simple attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # HTML template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: attachment.txt
        CONTENT-TYPE: text/html

        Hello world
    """), encoding="utf8")

    # Render in tmpdir
    with tmpdir.as_cwd():
        template_message = TemplateMessage(template_path)
        _, _, message = template_message.render({})

    # Verify that the message content type is HTML
    payload = message.get_payload()
    assert len(payload) == 2
    assert payload[0].get_content_type() == 'text/html'


def test_contenttype_attachment_markdown_body(tmpdir):
    """Content-type for MarkDown messages with attachments."""
    # Simple attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # HTML template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: attachment.txt
        CONTENT-TYPE: text/markdown

        Hello **world**
    """), encoding="utf8")

    # Render in tmpdir
    with tmpdir.as_cwd():
        template_message = TemplateMessage(template_path)
        _, _, message = template_message.render({})

    payload = message.get_payload()
    assert len(payload) == 2

    # Markdown: Make sure there is a plaintext part and an HTML part
    message_payload = payload[0].get_payload()
    assert len(message_payload) == 2

    # Ensure that the first part is plaintext and the second part
    # is HTML (as per RFC 2046)
    plaintext_part = message_payload[0]
    assert plaintext_part['Content-Type'].startswith("text/plain")

    html_part = message_payload[1]
    assert html_part['Content-Type'].startswith("text/html")


def test_duplicate_headers_attachment(tmp_path):
    """Verify multipart messages do not contain duplicate headers.

    Duplicate headers are rejected by some SMTP servers.
    """
    # Simple attachment
    attachment_path = Path(tmp_path/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # Simple message
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com>
        ATTACHMENT: attachment.txt

        {{message}}
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({
        "message": "Hello world"
    })

    # Verifty no duplicate headers
    assert len(message.keys()) == len(set(message.keys()))


def test_duplicate_headers_markdown(tmp_path):
    """Verify multipart messages do not contain duplicate headers.

    Duplicate headers are rejected by some SMTP servers.
    """
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com
        CONTENT-TYPE: text/markdown

        ```
        Message as code block: {{message}}
        ```
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({
        "message": "hello world",
    })

    # Verifty no duplicate headers
    assert len(message.keys()) == len(set(message.keys()))


def test_attachment_image_in_markdown(tmp_path):
    """Images sent as attachments should get linked correctly in images."""
    shutil.copy(str(utils.TESTDATA/"attachment_3.jpg"), str(tmp_path))

    # Create template .txt file
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>
        ATTACHMENT: attachment_3.jpg
        CONTENT-TYPE: text/markdown

        ![](./attachment_3.jpg)
    """), encoding="utf8")
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "email": "myself@mydomain.com"
    })

    # Verify sender and recipients
    assert sender == "My Self <myself@mydomain.com>"
    assert recipients == ["myself@mydomain.com"]

    # Verify message is multipart
    assert message.is_multipart()

    # Make sure there is a message body and the attachment
    payload = message.get_payload()
    assert len(payload) == 2

    # Markdown: Make sure there is a plaintext part and an HTML part
    message_payload = payload[0].get_payload()
    assert len(message_payload) == 2

    plaintext = extract_text_from_markdown_payload(message_payload[0],
                                                   'text/plain')
    htmltext = extract_text_from_markdown_payload(message_payload[1],
                                                  'text/html')

    assert plaintext.strip() == "![](./attachment_3.jpg)"

    attachments = extract_attachments(message)
    assert len(attachments) == 1
    filename, content, cid = attachments[0]
    cid = cid[1:-1]
    assert filename == "attachment_3.jpg"
    assert len(content) == 697

    expected = html5lib.parse(textwrap.dedent(f"""\
        <html><head />
        <body><p><img src="cid:{cid}" alt="" /></p></body>
        </html>
    """))
    assert html_docs_equal(html5lib.parse(htmltext), expected)


def test_content_id_header_for_attachments(tmpdir):
    """All attachments should get a content-id header."""
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: attachment.txt

        Hello world
    """), encoding="utf8")

    # Render in tmpdir
    with tmpdir.as_cwd():
        template_message = TemplateMessage(template_path)
        _, _, message = template_message.render({})

    # Verify message is multipart and contains attachment
    assert message.is_multipart()
    attachments = extract_attachments(message)
    assert len(attachments) == 1

    # Verify attachment
    filename, content, cid_header = attachments[0]
    assert filename == "attachment.txt"
    assert content == b"Hello world\n"
    assert re.match(r'<[\d\w]+(\.[\d\w]+)*@mailmerge\.invalid>', cid_header)

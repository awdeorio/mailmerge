# coding=utf-8
# Python 2 source containing unicode https://www.python.org/dev/peps/pep-0263/
"""
Tests for TemplateMessage.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
import re
import shutil
import textwrap
import collections
import pytest
import markdown
from mailmerge import TemplateMessage, MailmergeError
from . import utils

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path


def test_simple(tmp_path):
    """Render a simple template."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hello {{name}}!
    """))
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
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hello world!
    """))
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({})
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]
    plaintext = message.get_payload()
    assert "Hello world!" in plaintext


def test_multiple_substitutions(tmp_path):
    """Render a template with multiple context variables."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Hi, {{name}},

        Your number is {{number}}.
    """))
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
    template_path.write_text(u"TO: {{error_not_in_database}}")
    template_message = TemplateMessage(template_path)
    with pytest.raises(MailmergeError):
        template_message.render({"name": "Bob", "number": 17})


def test_cc_bcc(tmp_path):
    """CC recipients should receive a copy."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>
        CC: My Colleague <mycolleague@mydomain.com>
        BCC: Secret <secret@mydomain.com>

        Hello world
    """))
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


def test_html(tmp_path):
    """Verify HTML template results in a simple rendered message."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com
        Content-Type: text/html

        <html>
          <body>
            <p>{{message}}</p>
          </body>
        </html>
    """))
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
    htmltext = message.get_payload()
    htmltext = re.sub(r"\s+", "", htmltext)  # Strip whitespace
    assert htmltext == "<html><body><p>Helloworld</p></body></html>"


def test_html_plaintext(tmp_path):
    """Verify HTML and plaintest multipart template."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
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
    """))
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
    htmltext = html_part.get_payload()
    htmltext = re.sub(r"\s+", "", htmltext)  # Strip whitespace
    assert htmltext == "<html><body><p>Helloworld</p></body></html>"


def test_markdown(tmp_path):
    """Markdown messages should be converted to HTML."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
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
    """))
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

    # Make sure there is a plaintext part and an HTML part
    payload = message.get_payload()
    assert len(payload) == 2

    # Ensure that the first part is plaintext and the last part
    # is HTML (as per RFC 2046)
    plaintext_part = payload[0]
    assert plaintext_part['Content-Type'].startswith("text/plain")
    plaintext_encoding = str(plaintext_part.get_charset())
    plaintext = plaintext_part.get_payload(decode=True) \
                              .decode(plaintext_encoding)

    html_part = payload[1]
    assert html_part['Content-Type'].startswith("text/html")
    html_encoding = str(html_part.get_charset())
    htmltext = html_part.get_payload(decode=True) \
                        .decode(html_encoding)

    # Verify rendered Markdown
    rendered = markdown.markdown(plaintext)
    htmltext_correct = "<html><body>{}</body></html>".format(rendered)
    assert htmltext.strip() == htmltext_correct.strip()


def test_markdown_encoding(tmp_path):
    """Verify encoding is preserved when rendering a Markdown template.

    See Issue #59 for a detailed explanation
    https://github.com/awdeorio/mailmerge/issues/59
    """
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: test@example.com
        CONTENT-TYPE: text/markdown

        Hi, {{name}},
        æøå
    """))
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({
        "email": "myself@mydomain.com",
        "name": "Myself",
    })

    # Message should contain an unrendered Markdown plaintext part and a
    # rendered Markdown HTML part
    plaintext_part, html_part = message.get_payload()

    # Verify encodings
    assert str(plaintext_part.get_charset()) == "utf-8"
    assert str(html_part.get_charset()) == "utf-8"
    assert plaintext_part["Content-Transfer-Encoding"] == "base64"
    assert html_part["Content-Transfer-Encoding"] == "base64"

    # Verify content, which is base64 encoded
    plaintext = plaintext_part.get_payload(decode=True).decode("utf-8")
    htmltext = html_part.get_payload(decode=True).decode("utf-8")
    assert plaintext == u"Hi, Myself,\næøå"
    assert htmltext == u"<html><body><p>Hi, Myself,\næøå</p></body></html>"


Attachment = collections.namedtuple(
    "Attachment",
    ["filename", "content"],
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
            ))
    return attachments


def test_attachment_simple(tmpdir):
    """Verify a simple attachment."""
    # Simple attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text(u"Hello world\n")

    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: attachment.txt

        Hello world
    """))

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
    filename, content = attachments[0]
    assert filename == "attachment.txt"
    assert content == b"Hello world\n"


def test_attachment_relative(tmpdir):
    """Attachment with a relative file path is relative to template dir."""
    # Simple attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text(u"Hello world\n")

    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: attachment.txt

        Hello world
    """))

    # Render
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({})

    # Verify directory used to render is different from template directory
    assert os.getcwd() != tmpdir

    # Verify attachment
    attachments = extract_attachments(message)
    filename, content = attachments[0]
    assert filename == "attachment.txt"
    assert content == b"Hello world\n"


def test_attachment_absolute(tmpdir):
    """Attachment with absolute file path."""
    # Simple attachment lives in sub directory
    attachments_dir = tmpdir.mkdir("attachments")
    attachment_path = Path(attachments_dir/"attachment.txt")
    attachment_path.write_text(u"Hello world\n")

    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: {filename}

        Hello world
    """.format(filename=attachment_path)))

    # Render in tmpdir
    with tmpdir.as_cwd():
        template_message = TemplateMessage(template_path)
        _, _, message = template_message.render({})

    # Verify attachment
    attachments = extract_attachments(message)
    filename, content = attachments[0]
    assert filename == "attachment.txt"
    assert content == b"Hello world\n"


def test_attachment_template(tmpdir):
    """Attachment with template as part of file path."""
    # Simple attachment lives in sub directory
    attachments_dir = tmpdir.mkdir("attachments")
    attachment_path = Path(attachments_dir/"attachment.txt")
    attachment_path.write_text(u"Hello world\n")

    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: {{filename}}

        Hello world
    """))

    # Render in tmpdir
    with tmpdir.as_cwd():
        template_message = TemplateMessage(template_path)
        _, _, message = template_message.render({
            "filename": str(attachment_path),
        })

    # Verify attachment
    attachments = extract_attachments(message)
    filename, content = attachments[0]
    assert filename == "attachment.txt"
    assert content == b"Hello world\n"


def test_attachment_not_found(tmpdir):
    """Attachment file not found."""
    # Template specifying an attachment that doesn't exist
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: attachment.txt

        Hello world
    """))

    # Render in tmpdir, which lacks attachment.txt
    template_message = TemplateMessage(template_path)
    with pytest.raises(MailmergeError):
        with tmpdir.as_cwd():
            template_message.render({})


def test_attachment_blank(tmpdir):
    """Attachment header without a filename is an error."""
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT:

        Hello world
    """))
    template_message = TemplateMessage(template_path)
    with pytest.raises(MailmergeError) as err:
        with tmpdir.as_cwd():
            template_message.render({})
    assert "Empty attachment header" in str(err)


def test_attachment_tilde_path(tmpdir):
    """Attachment with home directory tilde notation file path."""
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        ATTACHMENT: ~/attachment.txt

        Hello world
    """))

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
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>
        ATTACHMENT: attachment_1.txt
        ATTACHMENT: attachment_2.pdf
        ATTACHMENT: attachment_{{number}}.txt

        Hi, {{name}},

        Your number is {{number}}.
    """))
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
    """Errr on empty attachment field."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com
        ATTACHMENT:

        Hello world
    """))
    template_message = TemplateMessage(template_path)
    with pytest.raises(MailmergeError):
        template_message.render({})


def test_utf8_template(tmp_path):
    """Verify UTF8 support in email template."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        From the Tagelied of Wolfram von Eschenbach (Middle High German):

        Sîne klâwen durh die wolken sint geslagen,
        er stîget ûf mit grôzer kraft,
        ich sih in grâwen tägelîch als er wil tagen,
        den tac, der im geselleschaft
        erwenden wil, dem werden man,
        den ich mit sorgen în verliez.
        ich bringe in hinnen, ob ich kan.
        sîn vil manegiu tugent michz leisten hiez.

        http://www.columbia.edu/~fdc/utf8/
    """))
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "email": "myself@mydomain.com",
    })

    # Verify encoding
    assert message.get_content_maintype() == "text"
    assert message.get_content_subtype() == "plain"
    assert message.get_content_charset() == "utf-8"

    # Verify sender and recipients
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]

    # Verify content
    plaintext = message.get_payload(decode=True).decode("utf-8")
    assert plaintext == textwrap.dedent(u"""\
        From the Tagelied of Wolfram von Eschenbach (Middle High German):

        Sîne klâwen durh die wolken sint geslagen,
        er stîget ûf mit grôzer kraft,
        ich sih in grâwen tägelîch als er wil tagen,
        den tac, der im geselleschaft
        erwenden wil, dem werden man,
        den ich mit sorgen în verliez.
        ich bringe in hinnen, ob ich kan.
        sîn vil manegiu tugent michz leisten hiez.

        http://www.columbia.edu/~fdc/utf8/""")


def test_utf8_database(tmp_path):
    """Verify UTF8 support when template is rendered with UTF-8 value."""
    # Simple template
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        Hi {{name}}
    """))

    # Render template with context containing unicode characters
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "name": u"Laȝamon",
    })

    # Verify sender and recipients
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]

    # Verify message encoding.  The template was ASCII, but when the template
    # is rendered with UTF-8 data, the result is UTF-8 encoding.
    assert message.get_content_maintype() == "text"
    assert message.get_content_subtype() == "plain"
    assert message.get_content_charset() == "utf-8"

    # Verify content
    plaintext = message.get_payload(decode=True).decode("utf-8")
    assert plaintext == u"Hi Laȝamon"


def test_emoji(tmp_path):
    """Verify emoji are encoded."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: test@test.com
        SUBJECT: Testing mailmerge
        FROM: test@test.com

        Hi 😀
    """))  # grinning face emoji
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({})

    # Verify encoding
    assert message.get_charset() == "utf-8"
    assert message["Content-Transfer-Encoding"] == "base64"

    # Verify content
    plaintext = message.get_payload(decode=True).decode("utf-8")
    assert plaintext == u"Hi 😀"


def test_emoji_markdown(tmp_path):
    """Verify emoji are encoded in Markdown formatted messages."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: test@example.com
        SUBJECT: Testing mailmerge
        FROM: test@example.com
        CONTENT-TYPE: text/markdown

        ```
        emoji_string = 😀
        ```
            """))  # grinning face emoji
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({})

    # Message should contain an unrendered Markdown plaintext part and a
    # rendered Markdown HTML part
    plaintext_part, html_part = message.get_payload()

    # Verify encodings
    assert str(plaintext_part.get_charset()) == "utf-8"
    assert str(html_part.get_charset()) == "utf-8"
    assert plaintext_part["Content-Transfer-Encoding"] == "base64"
    assert html_part["Content-Transfer-Encoding"] == "base64"

    # Verify content, which is base64 encoded grinning face emoji
    plaintext = plaintext_part.get_payload(decode=True).decode("utf-8")
    htmltext = html_part.get_payload(decode=True).decode("utf-8")
    assert plaintext == u'```\nemoji_string = \U0001f600\n```'
    assert htmltext == (
        u"<html><body><p><code>"
        u"emoji_string = \U0001f600"
        u"</code></p></body></html>"
    )


def test_emoji_database(tmp_path):
    """Verify emoji are encoded when they are substituted via template db.

    The template is ASCII encoded, but after rendering the template, an emoji
    character will substituted into the template.  The result should be a utf-8
    encoded message.
    """
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: test@test.com
        SUBJECT: Testing mailmerge
        FROM: test@test.com

        Hi {{emoji}}
    """))
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({
        "emoji": u"😀"  # grinning face
    })

    # Verify encoding
    assert message.get_charset() == "utf-8"
    assert message["Content-Transfer-Encoding"] == "base64"

    # Verify content
    plaintext = message.get_payload(decode=True).decode("utf-8")
    assert plaintext == u"Hi 😀"


def test_encoding_us_ascii(tmp_path):
    """Render a simple template with us-ascii encoding."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        Hello world
    """))
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({})
    assert message.get_charset() == "us-ascii"
    assert message.get_content_charset() == "us-ascii"
    assert message.get_payload() == "Hello world"


def test_encoding_utf8(tmp_path):
    """Render a simple template with UTF-8 encoding."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        Hello Laȝamon
    """))
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({})
    assert message.get_charset() == "utf-8"
    assert message.get_content_charset() == "utf-8"
    plaintext = message.get_payload(decode=True).decode("utf-8")
    assert plaintext == u"Hello Laȝamon"


def test_encoding_is8859_1(tmp_path):
    """Render a simple template with IS8859-1 encoding.

    Mailmerge will coerce the encoding to UTF-8.
    """
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        Hello L'Haÿ-les-Roses
    """))
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({})
    assert message.get_charset() == "utf-8"
    assert message.get_content_charset() == "utf-8"
    plaintext = message.get_payload(decode=True).decode("utf-8")
    assert plaintext == u"Hello L'Haÿ-les-Roses"


def test_encoding_mismatch(tmp_path):
    """Render a simple template that lies about its encoding.

    Header says us-ascii, but it contains utf-8.
    """
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        Content-Type: text/plain; charset="us-ascii"

        Hello Laȝamon
    """))
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({})
    assert message.get_charset() == "utf-8"
    assert message.get_content_charset() == "utf-8"
    plaintext = message.get_payload(decode=True).decode("utf-8")
    assert plaintext == u"Hello Laȝamon"


def test_encoding_multipart(tmp_path):
    """Render a utf-8 template with multipart encoding."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"

        This is a MIME-encoded message. If you are seeing this, your mail
        reader is old.

        --boundary
        Content-Type: text/plain; charset=utf-8

        Hello Laȝamon

        --boundary
        Content-Type: text/html; charset=utf-8

        <html>
          <body>
            <p>Hello Laȝamon</p>
          </body>
        </html>
    """))
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({})

    # Verify sender and recipients
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]

    # Should be multipart: plaintext and HTML
    assert message.is_multipart()
    parts = message.get_payload()
    assert len(parts) == 2
    plaintext_part, html_part = parts

    # Verify plaintext part
    assert plaintext_part.get_charset() == "utf-8"
    assert plaintext_part.get_content_charset() == "utf-8"
    assert plaintext_part.get_content_type() == "text/plain"
    plaintext = plaintext_part.get_payload(decode=True).decode("utf-8")
    plaintext = plaintext.strip()
    assert plaintext == u"Hello Laȝamon"

    # Verify html part
    assert html_part.get_charset() == "utf-8"
    assert html_part.get_content_charset() == "utf-8"
    assert html_part.get_content_type() == "text/html"
    htmltext = html_part.get_payload(decode=True).decode("utf-8")
    htmltext = re.sub(r"\s+", "", htmltext)  # Strip whitespace
    assert htmltext == u"<html><body><p>HelloLaȝamon</p></body></html>"


def test_encoding_multipart_mismatch(tmp_path):
    """Render a utf-8 template with multipart encoding and wrong headers.

    Content-Type headers say "us-ascii", but the message contains utf-8.
    """
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"

        This is a MIME-encoded message. If you are seeing this, your mail
        reader is old.

        --boundary
        Content-Type: text/plain; charset=us-ascii

        Hello Laȝamon

        --boundary
        Content-Type: text/html; charset=us-ascii

        <html>
          <body>
            <p>Hello Laȝamon</p>
          </body>
        </html>
    """))
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({})

    # Verify sender and recipients
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]

    # Should be multipart: plaintext and HTML
    assert message.is_multipart()
    parts = message.get_payload()
    assert len(parts) == 2
    plaintext_part, html_part = parts

    # Verify plaintext part
    assert plaintext_part.get_charset() == "utf-8"
    assert plaintext_part.get_content_charset() == "utf-8"
    assert plaintext_part.get_content_type() == "text/plain"
    plaintext = plaintext_part.get_payload(decode=True).decode("utf-8")
    plaintext = plaintext.strip()
    assert plaintext == u"Hello Laȝamon"

    # Verify html part
    assert html_part.get_charset() == "utf-8"
    assert html_part.get_content_charset() == "utf-8"
    assert html_part.get_content_type() == "text/html"
    htmltext = html_part.get_payload(decode=True).decode("utf-8")
    htmltext = re.sub(r"\s+", "", htmltext)  # Strip whitespace
    assert htmltext == u"<html><body><p>HelloLaȝamon</p></body></html>"

# coding=utf-8
# Python 2 source containing unicode https://www.python.org/dev/peps/pep-0263/
"""
Tests for TemplateMessage with different encodings.

Andrew DeOrio <awdeorio@umich.edu>
"""
import re
import textwrap
from mailmerge import TemplateMessage


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


def test_utf8_to(tmp_path):
    """Verify UTF8 support in TO field."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: Laȝamon <to@test.com>
        FROM: from@test.com

        {{message}}
    """))
    template_message = TemplateMessage(template_path)
    _, recipients, message = template_message.render({
        "message": "hello",
    })

    # Verify recipient name and email
    assert recipients == ["to@test.com"]
    assert message["to"] == u"Laȝamon <to@test.com>"


def test_utf8_from(tmp_path):
    """Verify UTF8 support in FROM field."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: Laȝamon <from@test.com>

        {{message}}
    """))
    template_message = TemplateMessage(template_path)
    sender, _, message = template_message.render({
        "message": "hello",
    })

    # Verify sender name and email
    assert sender == u"Laȝamon <from@test.com>"
    assert message["from"] == u"Laȝamon <from@test.com>"


def test_utf8_subject(tmp_path):
    """Verify UTF8 support in SUBJECT field."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
        SUBJECT: Laȝamon

        {{message}}
    """))
    template_message = TemplateMessage(template_path)
    _, _, message = template_message.render({
        "message": "hello",
    })

    # Verify subject
    assert message["subject"] == u"Laȝamon"


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

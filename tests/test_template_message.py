"""
Tests for TemplateMessage.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
import io
import shutil
import textwrap
import jinja2
import pytest
import markdown
from mailmerge.template_message import TemplateMessage
from . import utils

# Python 2.x UTF8 support requires csv backport
try:
    from backports import csv
except ImportError:
    import csv


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
    assert "Hello world!" in message.as_string()


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
    assert "Hello world!" in message.as_string()


def test_multiple_substitutions(tmp_path):
    """Render a template with multiple context variables."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>

        Hi, {{name}},

        Your number is {{number}}.
    """))
    template_message = TemplateMessage(template_path)
    sender, recipients, message = template_message.render({
        "email": "myself@mydomain.com",
        "name": "Myself",
        "number": 17,
    })
    assert sender == "My Self <myself@mydomain.com>"
    assert recipients == ["myself@mydomain.com"]
    assert "Hi, Myself," in message.as_string()
    assert "Your number is 17" in message.as_string()


def test_bad_jinja(tmp_path):
    """Bad jinja template should produce an error."""
    template_path = tmp_path / "template.txt"
    template_path.write_text("TO: {{error_not_in_database}}")
    template_message = TemplateMessage(template_path)
    with pytest.raises(jinja2.exceptions.UndefinedError):
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
    assert "BCC" not in message.as_string()
    assert "secret@mydomain.com" not in message.as_string()
    assert "Secret" not in message.as_string()


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
    plaintext_contenttype = payload[0]['Content-Type']
    assert plaintext_contenttype.startswith("text/plain")
    plaintext = payload[0].get_payload()
    html_contenttype = payload[1]['Content-Type']
    assert html_contenttype.startswith("text/html")

    # Verify rendered Markdown
    htmltext = payload[1].get_payload()
    rendered = markdown.markdown(plaintext)
    htmltext_correct = "<html><body>{}</body></html>".format(rendered)
    assert htmltext.strip() == htmltext_correct.strip()


def test_attachment(tmp_path):
    """Attachments should be sent as part of the email."""
    # Copy attachments
    shutil.copy(
        os.path.join(utils.TESTDATA, "attachment_1.txt"),
        tmp_path,
    )
    shutil.copy(
        os.path.join(utils.TESTDATA, "attachment_2.pdf"),
        tmp_path,
    )
    shutil.copy(
        os.path.join(utils.TESTDATA, "attachment_17.txt"),
        tmp_path,
    )

    # Create template .txt file
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>
        ATTACHMENT: attachment_1.txt
        ATTACHMENT: attachment_2.pdf
        ATTACHMENT: attachment_{{number}}.txt
        ATTACHMENT:

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
            filename_testdata = os.path.join(utils.TESTDATA, filename)
            with open(filename_testdata, 'rb') as expected_attachment:
                correct_file_contents = expected_attachment.read()
            assert file_contents == correct_file_contents
            expected_attachments[filename] = True
    assert email_body_present
    assert False not in expected_attachments.values()


def test_utf8_template():
    """Verify UTF8 support in email template."""
    template_message = TemplateMessage(
        template_path=os.path.join(utils.TESTDATA, "utf8_template.txt"),
    )
    sender, recipients, message = template_message.render({
        "email": "myself@mydomain.com",
    })

    # Verify encoding
    assert message.get_content_maintype() == "text"
    assert message.get_content_subtype() == "plain"
    assert message.get_content_charset() == "utf-8"

    # Verify sender and recipients
    assert sender == "My Self <myself@mydomain.com>"
    assert recipients == ["myself@mydomain.com"]

    # Verify content
    # NOTE: to decode a base46-encoded string:
    # print((str(base64.b64decode(payload), "utf-8")))
    payload = message.get_payload().replace("\n", "")
    assert payload == 'RnJvbSB0aGUgVGFnZWxpZWQgb2YgV29sZnJhbSB2b24gRXNjaGVuYmFjaCAoTWlkZGxlIEhpZ2ggR2VybWFuKToKClPDrm5lIGtsw6J3ZW4gZHVyaCBkaWUgd29sa2VuIHNpbnQgZ2VzbGFnZW4sCmVyIHN0w65nZXQgw7tmIG1pdCBncsO0emVyIGtyYWZ0LAppY2ggc2loIGluIGdyw6J3ZW4gdMOkZ2Vsw65jaCBhbHMgZXIgd2lsIHRhZ2VuLApkZW4gdGFjLCBkZXIgaW0gZ2VzZWxsZXNjaGFmdAplcndlbmRlbiB3aWwsIGRlbSB3ZXJkZW4gbWFuLApkZW4gaWNoIG1pdCBzb3JnZW4gw65uIHZlcmxpZXouCmljaCBicmluZ2UgaW4gaGlubmVuLCBvYiBpY2gga2FuLgpzw65uIHZpbCBtYW5lZ2l1IHR1Z2VudCBtaWNoeiBsZWlzdGVuIGhpZXouCgpodHRwOi8vd3d3LmNvbHVtYmlhLmVkdS9+ZmRjL3V0Zjgv'  # noqa: E501 pylint: disable=line-too-long


def test_utf8_database():
    """Verify UTF8 support when template is rendered with UTF-8 value."""
    template_message = TemplateMessage(
        template_path=os.path.join(utils.TESTDATA, "simple_template.txt"),
    )
    database_path = os.path.join(utils.TESTDATA, "utf8_database.csv")
    with io.open(database_path, "r") as database_file:
        reader = csv.DictReader(database_file)
        context = next(reader)
    sender, recipients, message = template_message.render(context)

    # Verify sender and recipients
    assert sender == "My Self <myself@mydomain.com>"
    assert recipients == ["myself@mydomain.com"]

    # Verify message encoding.  The template was ASCII, but when the template
    # is rendered with UTF-8 data, the result is UTF-8 encoding.
    assert message.get_content_maintype() == "text"
    assert message.get_content_subtype() == "plain"
    assert message.get_content_charset() == "utf-8"

    # Verify content
    # NOTE: to decode a base46-encoded string:
    # print((str(base64.b64decode(payload), "utf-8")))
    payload = message.get_payload()
    payload = message.get_payload().replace("\n", "")
    assert payload == 'SGksIExhyJ1hbW9uLAoKWW91ciBudW1iZXIgaXMgMTcu'

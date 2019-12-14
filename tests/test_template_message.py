"""
Tests for TemplateMessage.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
import io
import jinja2
import pytest
import markdown
import mailmerge.template_message
from . import utils

# Python 2.x UTF8 support requires csv backport
try:
    from backports import csv
except ImportError:
    import csv


def test_bad_jinja():
    """Bad jinja template should produce an error."""
    template_message = mailmerge.template_message.TemplateMessage(
        os.path.join(utils.TESTDATA, "bad_template.txt"),
    )
    with pytest.raises(jinja2.exceptions.UndefinedError):
        template_message.render({"name": "Bob", "number": 17})


def test_cc_bcc():
    """CC recipients should receive a copy."""
    template_message = mailmerge.template_message.TemplateMessage(
        template_path=os.path.join(utils.TESTDATA, "cc_bcc_template.txt"),
    )
    sender, recipients, message = template_message.render({
        "email": "myself@mydomain.com",
        "name": "Myself",
        "number": 17,
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


def test_markdown():
    """Markdown messages should be converted to HTML."""
    template_message = mailmerge.template_message.TemplateMessage(
        template_path=os.path.join(utils.TESTDATA, "markdown_template.txt"),
    )
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


def test_markdown_encoding():
    """Verify encoding is preserved when rendering a Markdown template.

    See Issue #59 for a detailed explanation
    https://github.com/awdeorio/mailmerge/issues/59
    """
    template_message = mailmerge.template_message.TemplateMessage(
        template_path=os.path.join(utils.TESTDATA, "markdown_template_utf8.txt"),
    )
    sender, recipients, message = template_message.render({
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
    plaintext = plaintext_part.get_payload().strip()
    htmltext = html_part.get_payload().strip()
    assert plaintext == "SGksIE15c2VsZiwKw6bDuMOl"
    assert htmltext == (
        "PGh0bWw+PGJvZHk+PHA+"
        "SGksIE15c2VsZiwKw6bDuMOl"
        "PC9wPjwvYm9keT48L2h0bWw+"
    )


def test_attachment():
    """Attachments should be sent as part of the email."""
    template_message = mailmerge.template_message.TemplateMessage(
        template_path=os.path.join(utils.TESTDATA, "attachment_template.txt"),
    )
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
    template_message = mailmerge.template_message.TemplateMessage(
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
    template_message = mailmerge.template_message.TemplateMessage(
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

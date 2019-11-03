"""Tests for MessageTemplate."""
import os
import jinja2
import pytest
import mailmerge
import markdown


# Directories containing test input files
# FIXME duplicate
TESTDIR = os.path.dirname(__file__)
TESTDATA = os.path.join(TESTDIR, "testdata")


def test_bad_jinja():
    """Bad jinja template should produce an error."""
    message_template = mailmerge.MessageTemplate(
        os.path.join(TESTDATA, "bad_template.txt"),
    )
    with pytest.raises(jinja2.exceptions.UndefinedError):
        message_template.render({"name": "Bob", "number": 17})


def test_cc_bcc():
    """CC recipients should receive a copy."""
    message_template = mailmerge.MessageTemplate(
        template_path=os.path.join(TESTDATA, "cc_bcc_template.txt"),
    )
    sender, recipients, message = message_template.render({
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
    message_template = mailmerge.MessageTemplate(
        template_path=os.path.join(TESTDATA, "markdown_template.txt"),
    )
    sender, recipients, message = message_template.render({
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


def test_attachment():
    """Attachments should be sent as part of the email."""
    message_template = mailmerge.MessageTemplate(
        template_path=os.path.join(TESTDATA, "attachment_template.txt"),
    )
    sender, recipients, message = message_template.render({
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
            filename_testdata = os.path.join(TESTDATA, filename)
            with open(filename_testdata, 'rb') as expected_attachment:
                correct_file_contents = expected_attachment.read()
            assert file_contents == correct_file_contents
            expected_attachments[filename] = True
    assert email_body_present
    assert False not in expected_attachments.values()


def test_utf8_template():
    """Verify UTF8 support in email template."""
    message_template = mailmerge.MessageTemplate(
        template_path=os.path.join(TESTDATA, "utf8_template.txt"),
    )
    sender, recipients, message = message_template.render({
        "email": "myself@mydomain.com",
        "name": "Myself",
        "number": 17,
    })

    # Verify encoding
    assert message.get_content_maintype() == "text"
    assert message.get_content_subtype() == "plain"
    assert message.get_content_charset() == "utf-8"

    # Verify content
    # NOTE: to decode a base46-encoded string:
    # print((str(base64.b64decode(payload), "utf-8")))
    payload = message.get_payload().replace("\n", "")
    assert payload == 'RnJvbSB0aGUgVGFnZWxpZWQgb2YgV29sZnJhbSB2b24gRXNjaGVuYmFjaCAoTWlkZGxlIEhpZ2ggR2VybWFuKToKClPDrm5lIGtsw6J3ZW4gZHVyaCBkaWUgd29sa2VuIHNpbnQgZ2VzbGFnZW4sCmVyIHN0w65nZXQgw7tmIG1pdCBncsO0emVyIGtyYWZ0LAppY2ggc2loIGluIGdyw6J3ZW4gdMOkZ2Vsw65jaCBhbHMgZXIgd2lsIHRhZ2VuLApkZW4gdGFjLCBkZXIgaW0gZ2VzZWxsZXNjaGFmdAplcndlbmRlbiB3aWwsIGRlbSB3ZXJkZW4gbWFuLApkZW4gaWNoIG1pdCBzb3JnZW4gw65uIHZlcmxpZXouCmljaCBicmluZ2UgaW4gaGlubmVuLCBvYiBpY2gga2FuLgpzw65uIHZpbCBtYW5lZ2l1IHR1Z2VudCBtaWNoeiBsZWlzdGVuIGhpZXouCgpodHRwOi8vd3d3LmNvbHVtYmlhLmVkdS9+ZmRjL3V0Zjgv'  # noqa: E501 pylint: disable=line-too-long

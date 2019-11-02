"""Mailmerge unit tests."""
import os
import email
import cd
import pytest
import markdown
import mailmerge


# NOTE: Python 2.x mock lives in a different place
try:
    from unittest import mock
except ImportError:
    import mock


# We're going to use mock_SMTP because it mimics the real SMTP library
# pylint: disable=invalid-name


# Directories containing test input files
TESTDIR = os.path.dirname(__file__)
TESTDATA = os.path.join(TESTDIR, "testdata")


def test_stdout(capsys):
    """Verify stdout and stderr.

    pytest docs on capturing stdout and stderr
    https://pytest.readthedocs.io/en/2.7.3/capture.html
    """
    mailmerge.api.main(
        database_path=os.path.join(TESTDATA, "simple_database.csv"),
        template_path=os.path.join(TESTDATA, "simple_template.txt"),
        config_path=os.path.join(TESTDATA, "server_open.conf"),
        limit=-1,
        dry_run=True,
    )

    # Verify mailmerge output
    stdout, stderr = capsys.readouterr()
    assert stderr == ""
    assert ">>> message 0" in stdout
    assert ">>> sent message 0" in stdout
    assert ">>> message 1" in stdout
    assert ">>> sent message 1" in stdout


@mock.patch('smtplib.SMTP')
def test_bad_jinja(mock_SMTP):
    """Bad jinja template should produce an error."""
    with pytest.raises(SystemExit):
        mailmerge.api.main(
            database_path=os.path.join(TESTDATA, "simple_database.csv"),
            template_path=os.path.join(TESTDATA, "bad_template.txt"),
            config_path=os.path.join(TESTDATA, "server_open.conf"),
            limit=1,
            dry_run=False,
        )

    # Verify no emails were sent
    smtp = mock_SMTP.return_value
    assert smtp.sendmail.call_count == 0


@mock.patch('smtplib.SMTP')
def test_smtp(mock_SMTP):
    """Verify SMTP library calls."""
    mailmerge.api.main(
        database_path=os.path.join(TESTDATA, "simple_database.csv"),
        template_path=os.path.join(TESTDATA, "simple_template.txt"),
        config_path=os.path.join(TESTDATA, "server_open.conf"),
        limit=1,
        dry_run=False,
    )

    # Mock smtp object with function calls recorded
    smtp = mock_SMTP.return_value
    assert smtp.sendmail.call_count == 1


@mock.patch('smtplib.SMTP')
def test_cc_bcc(mock_SMTP):
    """CC recipients should receive a copy."""
    mailmerge.api.main(
        database_path=os.path.join(TESTDATA, "simple_database.csv"),
        template_path=os.path.join(TESTDATA, "cc_bcc_template.txt"),
        config_path=os.path.join(TESTDATA, "server_open.conf"),
        limit=-1,
        dry_run=False,
    )

    # Parse sender and recipients from mock calls to sendmail
    smtp = mock_SMTP.return_value
    assert len(smtp.sendmail.call_args_list) == 1
    sender = smtp.sendmail.call_args_list[0][0][0]
    recipients = smtp.sendmail.call_args_list[0][0][1]
    raw_message = smtp.sendmail.call_args_list[0][0][2]

    # Verify recipients include CC and BCC
    assert sender == "My Self <myself@mydomain.com>"
    assert recipients == [
        "myself@mydomain.com",
        "mycolleague@mydomain.com",
        "secret@mydomain.com",
    ]

    # Make sure BCC recipients are *not* in the message
    assert "BCC" not in raw_message
    assert "secret@mydomain.com" not in raw_message
    assert "Secret" not in raw_message


@mock.patch('smtplib.SMTP')
def test_markdown(mock_SMTP):
    """Markdown messages should be converted to HTML before being sent."""
    mailmerge.api.main(
        database_path=os.path.join(TESTDATA, "simple_database.csv"),
        template_path=os.path.join(TESTDATA, "markdown_template.txt"),
        config_path=os.path.join(TESTDATA, "server_open.conf"),
        limit=1,
        dry_run=False,
    )

    # Parse sender, recipients and message from mock calls to sendmail
    smtp = mock_SMTP.return_value
    assert len(smtp.sendmail.call_args_list) == 1
    sender = smtp.sendmail.call_args_list[0][0][0]
    recipients = smtp.sendmail.call_args_list[0][0][1]
    raw_message = smtp.sendmail.call_args_list[0][0][2]
    message = email.parser.Parser().parsestr(raw_message)

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


@mock.patch('smtplib.SMTP')
def test_attachment(mock_SMTP):
    """Attachments should be sent as part of the email."""
    with cd.cd(TESTDATA):
        # Execute mailmerge inside testdata directory so that mailmerge can
        # find the attachment files
        mailmerge.api.main(
            database_path=os.path.join(TESTDATA, "simple_database.csv"),
            template_path=os.path.join(
                TESTDATA,
                "attachment_template.txt",
            ),
            config_path=os.path.join(TESTDATA, "server_open.conf"),
            limit=1,
            dry_run=False,
        )

    # Parse sender, recipients and message from mock calls to sendmail
    smtp = mock_SMTP.return_value
    assert len(smtp.sendmail.call_args_list) == 1
    sender = smtp.sendmail.call_args_list[0][0][0]
    recipients = smtp.sendmail.call_args_list[0][0][1]
    raw_message = smtp.sendmail.call_args_list[0][0][2]
    message = email.parser.Parser().parsestr(raw_message)

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


@mock.patch('smtplib.SMTP')
def test_utf8_template(mock_SMTP):
    """Verify UTF8 support in email template."""
    mailmerge.api.main(
        database_path=os.path.join(TESTDATA, "simple_database.csv"),
        template_path=os.path.join(TESTDATA, "utf8_template.txt"),
        config_path=os.path.join(TESTDATA, "server_open.conf"),
        limit=1,
        dry_run=False,
    )

    # Parse sender, recipients and message from mock calls to sendmail
    smtp = mock_SMTP.return_value
    assert len(smtp.sendmail.call_args_list) == 1
    raw_message = smtp.sendmail.call_args_list[0][0][2]
    message = email.parser.Parser().parsestr(raw_message)

    # Verify encoding
    assert message.get_content_maintype() == "text"
    assert message.get_content_subtype() == "plain"
    assert message.get_content_charset() == "utf-8"

    # Verify content
    # NOTE: to decode a base46-encoded string:
    # print((str(base64.b64decode(payload), "utf-8")))
    payload = message.get_payload().replace("\n", "")
    assert payload == 'RnJvbSB0aGUgVGFnZWxpZWQgb2YgV29sZnJhbSB2b24gRXNjaGVuYmFjaCAoTWlkZGxlIEhpZ2ggR2VybWFuKToKClPDrm5lIGtsw6J3ZW4gZHVyaCBkaWUgd29sa2VuIHNpbnQgZ2VzbGFnZW4sCmVyIHN0w65nZXQgw7tmIG1pdCBncsO0emVyIGtyYWZ0LAppY2ggc2loIGluIGdyw6J3ZW4gdMOkZ2Vsw65jaCBhbHMgZXIgd2lsIHRhZ2VuLApkZW4gdGFjLCBkZXIgaW0gZ2VzZWxsZXNjaGFmdAplcndlbmRlbiB3aWwsIGRlbSB3ZXJkZW4gbWFuLApkZW4gaWNoIG1pdCBzb3JnZW4gw65uIHZlcmxpZXouCmljaCBicmluZ2UgaW4gaGlubmVuLCBvYiBpY2gga2FuLgpzw65uIHZpbCBtYW5lZ2l1IHR1Z2VudCBtaWNoeiBsZWlzdGVuIGhpZXouCgpodHRwOi8vd3d3LmNvbHVtYmlhLmVkdS9+ZmRjL3V0Zjgv'  # noqa: E501 pylint: disable=line-too-long


@mock.patch('smtplib.SMTP')
def test_utf8_database(mock_SMTP):
    """Verify UTF8 support when template is rendered with UTF-8 value."""
    mailmerge.api.main(
        database_path=os.path.join(TESTDATA, "utf8_database.csv"),
        template_path=os.path.join(TESTDATA, "simple_template.txt"),
        config_path=os.path.join(TESTDATA, "server_open.conf"),
        limit=1,
        dry_run=False,
    )

    # Parse sender, recipients and message from mock calls to sendmail
    smtp = mock_SMTP.return_value
    assert len(smtp.sendmail.call_args_list) == 1
    sender = smtp.sendmail.call_args_list[0][0][0]
    recipients = smtp.sendmail.call_args_list[0][0][1]
    raw_message = smtp.sendmail.call_args_list[0][0][2]
    message = email.parser.Parser().parsestr(raw_message)

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


def test_enumerate_limit_no_limit():
    """Verify limit=-1 results in no early termination."""
    iterations = 0
    for i, a in mailmerge.api.enumerate_limit(["a", "b", "c"], -1):
        iterations += 1
    assert iterations == 3


def test_enumerate_limit_stop_early():
    """Verify limit results in early termination."""
    iterations = 0
    for i, a in mailmerge.api.enumerate_limit(["a", "b", "c"], 2):
        iterations += 1
    assert iterations == 2
    assert i == 1
    assert a == "b"


def test_enumerate_limit_zero():
    """Verify limit results in early termination."""
    iterations = 0
    for i, a in mailmerge.api.enumerate_limit(["a", "b", "c"], 0):
        iterations += 1
    assert iterations == 0

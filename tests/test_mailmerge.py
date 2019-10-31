"""Mailmerge unit tests."""
import os
import unittest.mock
import email
import cd
import markdown
import mailmerge


# We're going to use mock_SMTP because it mimics the real SMTP library
# pylint: disable=invalid-name


# Directories containing test input files
TEST_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(TEST_DIR, "testdata")


def test_stdout(capsys):
    """Verify stdout and stderr.

    pytest docs on capturing stdout and stderr
    https://pytest.readthedocs.io/en/2.7.3/capture.html
    """
    mailmerge.api.main(
        database_filename=os.path.join(TESTDATA_DIR, "simple_database.csv"),
        template_filename=os.path.join(TESTDATA_DIR, "simple_template.txt"),
        config_filename=os.path.join(TESTDATA_DIR, "server_open.conf"),
        no_limit=True,
    )

    # Verify mailmerge output
    stdout, stderr = capsys.readouterr()
    assert stderr == ""
    assert ">>> message 0" in stdout
    assert ">>> sent message 0 DRY RUN" in stdout
    assert ">>> message 1" in stdout
    assert ">>> sent message 1 DRY RUN" in stdout


@unittest.mock.patch('smtplib.SMTP')
def test_smtp(mock_SMTP):
    """Verify SMTP library calls."""
    mailmerge.api.main(
        database_filename=os.path.join(TESTDATA_DIR, "simple_database.csv"),
        template_filename=os.path.join(TESTDATA_DIR, "simple_template.txt"),
        config_filename=os.path.join(TESTDATA_DIR, "server_open.conf"),
        limit=1,
        dry_run=False,
    )

    # Mock smtp object with function calls recorded
    smtp = mock_SMTP.return_value
    assert smtp.sendmail.call_count == 1


@unittest.mock.patch('smtplib.SMTP')
def test_cc_bcc(mock_SMTP):
    """CC recipients should receive a copy."""
    mailmerge.api.main(
        database_filename=os.path.join(TESTDATA_DIR, "simple_database.csv"),
        template_filename=os.path.join(TESTDATA_DIR, "cc_bcc_template.txt"),
        config_filename=os.path.join(TESTDATA_DIR, "server_open.conf"),
        dry_run=False,
        no_limit=False,
    )

    # Parse sender and recipients from mock calls to sendmail
    smtp = mock_SMTP.return_value
    assert len(smtp.sendmail.call_args_list) == 1
    sender = smtp.sendmail.call_args_list[0][0][0]
    recipients = smtp.sendmail.call_args_list[0][0][1]
    message = smtp.sendmail.call_args_list[0][0][2]

    # Verify recipients include CC and BCC
    assert sender == "My Self <myself@mydomain.com>"
    assert recipients == [
        "myself@mydomain.com",
        "mycolleague@mydomain.com",
        "secret@mydomain.com",
    ]

    # Make sure BCC recipients are *not* in the message
    assert "BCC" not in message
    assert "secret@mydomain.com" not in message
    assert "Secret" not in message


@unittest.mock.patch('smtplib.SMTP')
def test_markdown(mock_SMTP):
    """Markdown messages should be converted to HTML before being sent."""
    mailmerge.api.main(
        database_filename=os.path.join(TESTDATA_DIR, "simple_database.csv"),
        template_filename=os.path.join(TESTDATA_DIR, "markdown_template.txt"),
        config_filename=os.path.join(TESTDATA_DIR, "server_open.conf"),
        no_limit=False,
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
    assert f"<html><body>{rendered}</body></html>" == htmltext.strip()


@unittest.mock.patch('smtplib.SMTP')
def test_attachment(mock_SMTP):
    """Attachments should be sent as part of the email."""
    with cd.cd(TESTDATA_DIR):
        mailmerge.api.main(
            database_filename=os.path.join(TESTDATA_DIR, "simple_database.csv"),
            template_filename=os.path.join(TESTDATA_DIR, "attachment_template.txt"),
            config_filename=os.path.join(TESTDATA_DIR, "server_open.conf"),
            no_limit=False,
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
            filename_testdata = os.path.join(TESTDATA_DIR, filename)
            with open(filename_testdata, 'rb') as expected_attachment:
                correct_file_contents = expected_attachment.read()
            assert file_contents == correct_file_contents
            expected_attachments[filename] = True
    assert email_body_present
    assert False not in expected_attachments.values()

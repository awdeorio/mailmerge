"""Mailmerge unit tests."""
import os
import unittest.mock
import mailmerge


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
def test_smtp(SMTP):
    """Verify SMTP library calls."""
    mailmerge.api.main(
        database_filename=os.path.join(TESTDATA_DIR, "simple_database.csv"),
        template_filename=os.path.join(TESTDATA_DIR, "simple_template.txt"),
        config_filename=os.path.join(TESTDATA_DIR, "server_open.conf"),
        limit=1,
        dry_run=False,
    )

    # Mock smtp object with function calls recorded
    smtp = SMTP.return_value
    assert smtp.sendmail.call_count == 1


@unittest.mock.patch('smtplib.SMTP')
def test_cc_bcc(SMTP):
    """CC recipients should receive a copy."""
    mailmerge.api.main(
        database_filename=os.path.join(TESTDATA_DIR, "simple_database.csv"),
        template_filename=os.path.join(TESTDATA_DIR, "test_cc_bcc_template.txt"),
        config_filename=os.path.join(TESTDATA_DIR, "server_open.conf"),
        dry_run=False,
        no_limit=False,
    )

    # Parse sender and recipients from mock calls to sendmail
    smtp = SMTP.return_value
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

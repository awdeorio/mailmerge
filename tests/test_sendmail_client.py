"""
Tests for SendmailClient.

Andrew DeOrio <awdeorio@umich.edu>
"""
import textwrap
import future.backports.email as email
import future.backports.email.parser  # pylint: disable=unused-import
from mailmerge.sendmail_client import SendmailClient

try:
    from unittest import mock  # Python 3
except ImportError:
    import mock  # Python 2


# We're going to use mock_SMTP because it mimics the real SMTP library
# pylint: disable=invalid-name


@mock.patch('smtplib.SMTP')
def test_smtp(mock_SMTP, tmp_path):
    """Verify SMTP library calls."""
    config_path = tmp_path/"config.conf"
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        security = Never
    """))
    sendmail_client = SendmailClient(
        config_path,
        dry_run=False,
    )
    message = email.message_from_string(u"""
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hello world
    """)

    sendmail_client.sendmail(
        sender="from@test.com",
        recipients=["to@test.com"],
        message=message,
    )

    # Mock smtp object with function calls recorded
    smtp = mock_SMTP.return_value
    assert smtp.sendmail.call_count == 1


@mock.patch('smtplib.SMTP')
def test_dry_run(mock_SMTP, tmp_path):
    """Verify no sendmail() calls when dry_run=True."""
    config_path = tmp_path/"config.conf"
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        security = Never
    """))
    sendmail_client = SendmailClient(
        config_path,
        dry_run=True,
    )
    message = email.message_from_string(u"""
        TO: test@test.com
        SUBJECT: Testing mailmerge
        FROM: test@test.com

        Hello world
    """)

    sendmail_client.sendmail(
        sender="from@test.com",
        recipients=["to@test.com"],
        message=message,
    )

    # Mock smtp object with function calls recorded
    smtp = mock_SMTP.return_value
    assert smtp.sendmail.call_count == 0

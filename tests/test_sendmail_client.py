"""
Tests for SendmailClient.

Andrew DeOrio <awdeorio@umich.edu>
"""
import textwrap
import configparser
import pytest
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
@mock.patch('getpass.getpass')
def test_dry_run(mock_getpass, mock_SMTP, tmp_path):
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

    # Verify SMTP wasn't called and password wasn't used
    assert mock_getpass.call_count == 0
    smtp = mock_SMTP.return_value
    assert smtp.sendmail.call_count == 0


@mock.patch('smtplib.SMTP_SSL')
@mock.patch('getpass.getpass')
def test_no_dry_run(mock_getpass, mock_SMTP_SSL, tmp_path):
    """Verify --no-dry-run calls SMTP sendmail()."""
    config_path = tmp_path/"config.conf"
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 465
        security = SSL/TLS
        username = admin
    """))
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string(u"""
        TO: test@test.com
        SUBJECT: Testing mailmerge
        FROM: test@test.com

        Hello world
    """)

    # Mock the password entry
    mock_getpass.return_value = "password"

    # Send a message
    sendmail_client.sendmail(
        sender="from@test.com",
        recipients=["to@test.com"],
        message=message,
    )

    # Verify function calls for password and sendmail()
    assert mock_getpass.call_count == 1
    smtp = mock_SMTP_SSL.return_value
    assert smtp.sendmail.call_count == 1


def test_bad_config(tmp_path):
    """Verify bad config file throws an exception."""
    config_path = tmp_path/"config.conf"
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        badkey = open-smtp.example.com
    """))
    with pytest.raises(configparser.Error):
        SendmailClient(config_path, dry_run=True)


@mock.patch('smtplib.SMTP')
@mock.patch('smtplib.SMTP_SSL')
@mock.patch('getpass.getpass')
def test_security_open(mock_getpass, mock_SMTP_SSL, mock_SMTP, tmp_path):
    """Verify open (Never) security configuration."""
    # Config for no security SMTP server
    config_path = tmp_path/"config.conf"
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        security = Never
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string(u"Hello world")

    # Mock the password entry
    mock_getpass.return_value = "password"

    # Send a message
    sendmail_client.sendmail(
        sender="test@test.com",
        recipients=["test@test.com"],
        message=message,
    )

    # Verify SMTP library calls
    assert mock_getpass.call_count == 0
    assert mock_SMTP.call_count == 1
    assert mock_SMTP_SSL.call_count == 0
    smtp = mock_SMTP.return_value
    assert smtp.sendmail.call_count == 1
    assert smtp.login.call_count == 0


@mock.patch('smtplib.SMTP')
@mock.patch('smtplib.SMTP_SSL')
@mock.patch('getpass.getpass')
def test_security_starttls(mock_getpass, mock_SMTP_SSL, mock_SMTP, tmp_path):
    """Verify open (Never) security configuration."""
    # Config for no security SMTP server
    config_path = tmp_path/"config.conf"
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = newman.eecs.umich.edu
        port = 25
        security = STARTTLS
        username = YOUR_USERNAME_HERE
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string(u"Hello world")

    # Mock the password entry
    mock_getpass.return_value = "password"

    # Send a message
    sendmail_client.sendmail(
        sender="test@test.com",
        recipients=["test@test.com"],
        message=message,
    )

    # Verify SMTP library calls
    assert mock_getpass.call_count == 1
    assert mock_SMTP.call_count == 1
    assert mock_SMTP_SSL.call_count == 0
    smtp = mock_SMTP.return_value
    assert smtp.ehlo.call_count == 2
    assert smtp.starttls.call_count == 1
    assert smtp.login.call_count == 1
    assert smtp.sendmail.call_count == 1

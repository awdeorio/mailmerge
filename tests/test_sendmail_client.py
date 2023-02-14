"""
Tests for SendmailClient.

Andrew DeOrio <awdeorio@umich.edu>
"""
import textwrap
import socket
import smtplib
import email
import email.parser
import pytest
from mailmerge import SendmailClient, MailmergeError


def test_smtp(mocker, tmp_path):
    """Verify SMTP library calls."""
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))
    sendmail_client = SendmailClient(
        config_path,
        dry_run=False,
    )
    message = email.message_from_string("""
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hello world
    """)

    # Execute sendmail with mock SMTP
    mock_smtp = mocker.patch('smtplib.SMTP')
    sendmail_client.sendmail(
        sender="from@test.com",
        recipients=["to@test.com"],
        message=message,
    )

    # Mock smtp object with function calls recorded
    smtp = mock_smtp.return_value.__enter__.return_value
    assert smtp.sendmail.call_count == 1


def test_dry_run(mocker, tmp_path):
    """Verify no sendmail() calls when dry_run=True."""
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        security = Never
    """))
    sendmail_client = SendmailClient(
        config_path,
        dry_run=True,
    )
    message = email.message_from_string("""
        TO: test@test.com
        SUBJECT: Testing mailmerge
        FROM: test@test.com

        Hello world
    """)

    # Execute sendmail with mock SMTP and getpass
    mock_smtp = mocker.patch('smtplib.SMTP')
    mock_getpass = mocker.patch('getpass.getpass')
    sendmail_client.sendmail(
        sender="from@test.com",
        recipients=["to@test.com"],
        message=message,
    )

    # Verify SMTP wasn't called and password wasn't used
    assert mock_getpass.call_count == 0
    smtp = mock_smtp.return_value.__enter__.return_value
    assert smtp.sendmail.call_count == 0


def test_no_dry_run(mocker, tmp_path):
    """Verify --no-dry-run calls SMTP sendmail()."""
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 465
        security = SSL/TLS
        username = admin
    """))
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string("""
        TO: test@test.com
        SUBJECT: Testing mailmerge
        FROM: test@test.com

        Hello world
    """)

    # Mock the password entry and SMTP
    mock_smtp_ssl = mocker.patch('smtplib.SMTP_SSL')
    mock_getpass = mocker.patch('getpass.getpass')
    mock_getpass.return_value = "password"

    # Execute sendmail
    sendmail_client.sendmail(
        sender="from@test.com",
        recipients=["to@test.com"],
        message=message,
    )

    # Verify function calls for password and sendmail()
    assert mock_getpass.call_count == 1
    smtp = mock_smtp_ssl.return_value.__enter__.return_value
    assert smtp.sendmail.call_count == 1


def test_bad_config_key(tmp_path):
    """Verify config file with bad key throws an exception."""
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        badkey = open-smtp.example.com
    """))
    with pytest.raises(MailmergeError):
        SendmailClient(config_path, dry_run=True)


def test_security_error(tmp_path):
    """Verify config file with bad security type throws an exception."""
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = smtp.mail.umich.edu
        port = 465
        security = bad_value
        username = YOUR_USERNAME_HERE
    """))
    with pytest.raises(MailmergeError):
        SendmailClient(config_path, dry_run=False)


def test_security_open(mocker, tmp_path):
    """Verify open (Never) security configuration."""
    # Config for no security SMTP server
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string("Hello world")

    # Mock SMTP and getpass
    mock_smtp = mocker.patch('smtplib.SMTP')
    mock_smtp_ssl = mocker.patch('smtplib.SMTP_SSL')
    mock_getpass = mocker.patch('getpass.getpass')

    # Send a message
    sendmail_client.sendmail(
        sender="test@test.com",
        recipients=["test@test.com"],
        message=message,
    )

    # Verify SMTP library calls
    assert mock_getpass.call_count == 0
    assert mock_smtp.call_count == 1
    assert mock_smtp_ssl.call_count == 0
    smtp = mock_smtp.return_value.__enter__.return_value
    assert smtp.sendmail.call_count == 1
    assert smtp.login.call_count == 0


def test_security_open_legacy(mocker, tmp_path):
    """Verify legacy "security = Never" configuration."""
    # Config SMTP server with "security = Never" legacy option
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        security = Never
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string("Hello world")

    # Mock SMTP
    mock_smtp = mocker.patch('smtplib.SMTP')

    # Send a message
    sendmail_client.sendmail(
        sender="test@test.com",
        recipients=["test@test.com"],
        message=message,
    )

    # Verify SMTP library calls
    smtp = mock_smtp.return_value.__enter__.return_value
    assert smtp.sendmail.call_count == 1


def test_security_starttls(mocker, tmp_path):
    """Verify open (Never) security configuration."""
    # Config for STARTTLS SMTP server
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = newman.eecs.umich.edu
        port = 25
        security = STARTTLS
        username = YOUR_USERNAME_HERE
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string("Hello world")

    # Mock SMTP
    mock_smtp = mocker.patch('smtplib.SMTP')
    mock_smtp_ssl = mocker.patch('smtplib.SMTP_SSL')

    # Mock the password entry
    mock_getpass = mocker.patch('getpass.getpass')
    mock_getpass.return_value = "password"

    # Send a message
    sendmail_client.sendmail(
        sender="test@test.com",
        recipients=["test@test.com"],
        message=message,
    )

    # Verify SMTP library calls
    assert mock_getpass.call_count == 1
    assert mock_smtp.call_count == 1
    assert mock_smtp_ssl.call_count == 0
    smtp = mock_smtp.return_value.__enter__.return_value
    assert smtp.ehlo.call_count == 2
    assert smtp.starttls.call_count == 1
    assert smtp.login.call_count == 1
    assert smtp.sendmail.call_count == 1


def test_security_plain(mocker, tmp_path):
    """Verify plain security configuration."""
    # Config for Plain SMTP server
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = newman.eecs.umich.edu
        port = 25
        security = PLAIN
        username = YOUR_USERNAME_HERE
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string("Hello world")

    # Mock SMTP
    mock_smtp = mocker.patch('smtplib.SMTP')
    mock_smtp_ssl = mocker.patch('smtplib.SMTP_SSL')

    # Mock the password entry
    mock_getpass = mocker.patch('getpass.getpass')
    mock_getpass.return_value = "password"

    # Send a message
    sendmail_client.sendmail(
        sender="test@test.com",
        recipients=["test@test.com"],
        message=message,
    )

    # Verify SMTP library calls
    assert mock_getpass.call_count == 1
    assert mock_smtp.call_count == 1
    assert mock_smtp_ssl.call_count == 0
    smtp = mock_smtp.return_value.__enter__.return_value
    assert smtp.ehlo.call_count == 0
    assert smtp.starttls.call_count == 0
    assert smtp.login.call_count == 1
    assert smtp.sendmail.call_count == 1


def test_security_ssl(mocker, tmp_path):
    """Verify open (Never) security configuration."""
    # Config for SSL SMTP server
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = smtp.mail.umich.edu
        port = 465
        security = SSL/TLS
        username = YOUR_USERNAME_HERE
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string("Hello world")

    # Mock SMTP
    mock_smtp = mocker.patch('smtplib.SMTP')
    mock_smtp_ssl = mocker.patch('smtplib.SMTP_SSL')

    # Mock the password entry
    mock_getpass = mocker.patch('getpass.getpass')
    mock_getpass.return_value = "password"

    # Send a message
    sendmail_client.sendmail(
        sender="test@test.com",
        recipients=["test@test.com"],
        message=message,
    )

    # Verify SMTP library calls
    assert mock_getpass.call_count == 1
    assert mock_smtp.call_count == 0
    assert mock_smtp_ssl.call_count == 1
    smtp = mock_smtp_ssl.return_value.__enter__.return_value
    assert smtp.ehlo.call_count == 0
    assert smtp.starttls.call_count == 0
    assert smtp.login.call_count == 1
    assert smtp.sendmail.call_count == 1


def test_missing_username(tmp_path):
    """Verify exception on missing username."""
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = smtp.mail.umich.edu
        port = 465
        security = SSL/TLS
    """))
    with pytest.raises(MailmergeError):
        SendmailClient(config_path, dry_run=False)


def test_smtp_login_error(mocker, tmp_path):
    """Login failure."""
    # Config for SSL SMTP server
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = smtp.gmail.com
        port = 465
        security = SSL/TLS
        username = awdeorio
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string("Hello world")

    # Mock SMTP and getpass
    mock_smtp_ssl = mocker.patch('smtplib.SMTP_SSL')

    # Mock the password entry
    mock_getpass = mocker.patch('getpass.getpass')
    mock_getpass.return_value = "password"

    # Configure SMTP login() to raise an exception
    mock_smtp_ssl.return_value.__enter__.return_value.login = mocker.Mock(
        side_effect=smtplib.SMTPAuthenticationError(
            code=535,
            msg=(
                "5.7.8 Username and Password not accepted. Learn more at "
                "5.7.8  https://support.google.com/mail/?p=BadCredentials "
                "xyzxyz.32 - gsmtp"
            )
        )
    )

    # Send a message
    with pytest.raises(MailmergeError) as err:
        sendmail_client.sendmail(
            sender="test@test.com",
            recipients=["test@test.com"],
            message=message,
        )

    # Verify exception string
    assert "smtp.gmail.com:465 failed to authenticate user 'awdeorio'" in\
        str(err.value)
    assert "535" in str(err.value)
    assert (
        "5.7.8 Username and Password not accepted. Learn more at "
        "5.7.8  https://support.google.com/mail/?p=BadCredentials "
        "xyzxyz.32 - gsmtp"
    ) in str(err.value)


def test_smtp_sendmail_error(mocker, tmp_path):
    """Failure during SMTP protocol."""
    # Config for SSL SMTP server
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = smtp.gmail.com
        port = 465
        security = SSL/TLS
        username = awdeorio
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string("Hello world")

    # Mock SMTP
    mock_smtp_ssl = mocker.patch('smtplib.SMTP_SSL')

    # Mock the password entry
    mock_getpass = mocker.patch('getpass.getpass')
    mock_getpass.return_value = "password"

    # Configure SMTP sendmail() to raise an exception
    mock_smtp_ssl.return_value.__enter__.return_value.sendmail = mocker.Mock(
        side_effect=smtplib.SMTPException("Dummy error message")
    )

    # Send a message
    with pytest.raises(MailmergeError) as err:
        sendmail_client.sendmail(
            sender="test@test.com",
            recipients=["test@test.com"],
            message=message,
        )

    # Verify exception string
    assert "Dummy error message" in str(err.value)


def test_socket_error(mocker, tmp_path):
    """Failed socket connection."""
    # Config for SSL SMTP server
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = smtp.gmail.com
        port = 465
        security = SSL/TLS
        username = awdeorio
    """))

    # Simple template
    sendmail_client = SendmailClient(config_path, dry_run=False)
    message = email.message_from_string("Hello world")

    # Mock SMTP
    mock_smtp_ssl = mocker.patch('smtplib.SMTP_SSL')

    # Mock the password entry
    mock_getpass = mocker.patch('getpass.getpass')
    mock_getpass.return_value = "password"

    # Configure SMTP_SSL constructor to raise an exception
    mock_smtp_ssl.return_value.__enter__ = mocker.Mock(
        side_effect=socket.error("Dummy error message")
    )

    # Send a message
    with pytest.raises(MailmergeError) as err:
        sendmail_client.sendmail(
            sender="test@test.com",
            recipients=["test@test.com"],
            message=message,
        )

    # Verify exception string
    assert "Dummy error message" in str(err.value)

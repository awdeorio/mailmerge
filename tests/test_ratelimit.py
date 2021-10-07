"""
Tests for SMTP server rate limit feature.

Andrew DeOrio <awdeorio@umich.edu>
"""
import textwrap
import datetime
from pathlib import Path
import email
import email.parser
import freezegun
import pytest
import click.testing
from mailmerge import SendmailClient, MailmergeRateLimitError
from mailmerge.__main__ import main


def test_sendmail_ratelimit(mocker, tmp_path):
    """Verify SMTP library calls."""
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        ratelimit = 60
    """), encoding="utf8")
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

    # Mock SMTP
    mock_smtp = mocker.patch('smtplib.SMTP')

    # First message
    sendmail_client.sendmail(
        sender="from@test.com",
        recipients=["to@test.com"],
        message=message,
    )
    smtp = mock_smtp.return_value.__enter__.return_value
    assert smtp.sendmail.call_count == 1

    # Second message exceeds the rate limit, doesn't try to send a message
    with pytest.raises(MailmergeRateLimitError):
        sendmail_client.sendmail(
            sender="from@test.com",
            recipients=["to@test.com"],
            message=message,
        )
    assert smtp.sendmail.call_count == 1

    # Retry the second message after 1 s because the rate limit is 60 messages
    # per minute
    #
    # Mock the time to be 1.1 s in the future
    # Ref: https://github.com/spulec/freezegun
    now = datetime.datetime.now()
    with freezegun.freeze_time(now + datetime.timedelta(seconds=1)):
        sendmail_client.sendmail(
            sender="from@test.com",
            recipients=["to@test.com"],
            message=message,
        )
    assert smtp.sendmail.call_count == 2


def test_stdout_ratelimit(mocker, tmpdir):
    """Verify SMTP server ratelimit parameter."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: from@test.com

        Hello world
    """), encoding="utf8")

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email
        one@test.com
        two@test.com
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        ratelimit = 60
    """), encoding="utf8")

    # Mock SMTP
    mock_smtp = mocker.patch('smtplib.SMTP')

    # Run mailmerge
    before = datetime.datetime.now()
    with tmpdir.as_cwd():
        runner = click.testing.CliRunner(mix_stderr=False)
        result = runner.invoke(
            main, [
                "--no-limit",
                "--no-dry-run",
                "--output-format", "text",
            ]
        )
    after = datetime.datetime.now()
    assert after - before > datetime.timedelta(seconds=1)
    smtp = mock_smtp.return_value.__enter__.return_value
    assert smtp.sendmail.call_count == 2
    assert result.exit_code == 0
    assert result.stderr == ""
    assert ">>> message 1 sent" in result.stdout
    assert ">>> rate limit exceeded, waiting ..." in result.stdout
    assert ">>> message 2 sent" in result.stdout

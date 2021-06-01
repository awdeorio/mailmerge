# coding=utf-8
# Python 2 source containing unicode https://www.python.org/dev/peps/pep-0263/
"""
Tests for SMTP server rate limit feature.

Andrew DeOrio <awdeorio@umich.edu>
"""
import textwrap
import datetime
import future.backports.email as email
import future.backports.email.parser  # pylint: disable=unused-import
import freezegun
import pytest
import click
import click.testing
from mailmerge import SendmailClient, MailmergeRateLimitError
from mailmerge.__main__ import main

try:
    from unittest import mock  # Python 3
except ImportError:
    import mock  # Python 2

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

# The sh library triggers lot of false no-member errors
# pylint: disable=no-member

# We're going to use mock_SMTP because it mimics the real SMTP library
# pylint: disable=invalid-name


@mock.patch('smtplib.SMTP')
def test_sendmail_ratelimit(mock_SMTP, tmp_path):
    """Verify SMTP library calls."""
    config_path = tmp_path/"server.conf"
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        ratelimit = 60
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

    # First message
    sendmail_client.sendmail(
        sender="from@test.com",
        recipients=["to@test.com"],
        message=message,
    )
    smtp = mock_SMTP.return_value.__enter__.return_value
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


@mock.patch('smtplib.SMTP')
def test_stdout_ratelimit(mock_SMTP, tmpdir):
    """Verify SMTP server ratelimit parameter."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Hello world
    """))

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        one@test.com
        two@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        ratelimit = 60
    """))

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
    smtp = mock_SMTP.return_value.__enter__.return_value
    assert smtp.sendmail.call_count == 2
    assert result.exit_code == 0
    # assert result.stderr == ""  # replace when we drop Python 3.4 support
    assert ">>> message 1 sent" in result.stdout
    assert ">>> rate limit exceeded, waiting ..." in result.stdout
    assert ">>> message 2 sent" in result.stdout

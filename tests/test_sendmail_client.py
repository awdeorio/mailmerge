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
    message = email.parser.Parser().parsestr(u"""
    TO: bob@bobdomain.com
    SUBJECT: Testing mailmerge
    FROM: My Self <myself@mydomain.com>

    Hi, Bob,
    """)

    sendmail_client.sendmail(
        sender="myself@mydomain.com",
        recipients=["bob@bobdomain.com"],
        message=message,
    )

    # Mock smtp object with function calls recorded
    smtp = mock_SMTP.return_value
    assert smtp.sendmail.call_count == 1

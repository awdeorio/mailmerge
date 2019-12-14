"""
Tests for SendmailClient.

Andrew DeOrio <awdeorio@umich.edu>
"""
import future.backports.email as email
import future.backports.email.parser  # pylint: disable=unused-import
from mailmerge.sendmail_client import SendmailClient
from . import utils

try:
    from unittest import mock  # Python 3
except ImportError:
    import mock  # Python 2


# We're going to use mock_SMTP because it mimics the real SMTP library
# pylint: disable=invalid-name


@mock.patch('smtplib.SMTP')
def test_smtp(mock_SMTP):
    """Verify SMTP library calls."""
    sendmail_client = SendmailClient(
        utils.TESTDATA/"server_open.conf",
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

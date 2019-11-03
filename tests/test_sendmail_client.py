"""Tests for SendmailClient."""
import os
import future.backports.email as email
import future.backports.email.parser
from mailmerge.sendmail_client import SendmailClient
from . import utils

# NOTE: Python 2.x mock lives in a different place
try:
    from unittest import mock
except ImportError:
    import mock


# We're going to use mock_SMTP because it mimics the real SMTP library
# pylint: disable=invalid-name


@mock.patch('smtplib.SMTP')
def test_smtp(mock_SMTP):
    """Verify SMTP library calls."""
    sendmail_client = SendmailClient(
        os.path.join(utils.TESTDATA, "server_open.conf"),
        dry_run=False,
    )
    message = email.parser.Parser().parsestr("""
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

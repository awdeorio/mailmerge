"""Mailmerge system tests."""
import os
import email
import sh
import utils
import mailmerge.api


# NOTE: Python 2.x mock lives in a different place
try:
    from unittest import mock
except ImportError:
    import mock


# We're going to use mock_SMTP because it mimics the real SMTP library
# pylint: disable=invalid-name


def test_stdout():
    """Verify stdout and stderr.

    pytest docs on capturing stdout and stderr
    https://pytest.readthedocs.io/en/2.7.3/capture.html
    """
    mailmerge_cmd = sh.Command("mailmerge")
    output = mailmerge_cmd(
        "--template", os.path.join(utils.TESTDATA, "simple_template.txt"),
        "--database", os.path.join(utils.TESTDATA, "simple_database.csv"),
        "--config", os.path.join(utils.TESTDATA, "server_open.conf"),
        "--no-limit",
        "--dry-run",
    )

    # Verify mailmerge output
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")
    assert stderr == ""
    assert ">>> message 0" in stdout
    assert ">>> sent message 0" in stdout
    assert ">>> message 1" in stdout
    assert ">>> sent message 1" in stdout


@mock.patch('smtplib.SMTP')
def test_smtp(mock_SMTP):
    """Verify SMTP library calls."""
    mailmerge_cmd = sh.Command("mailmerge")
    output = mailmerge_cmd(
        "--template", os.path.join(utils.TESTDATA, "simple_template.txt"),
        "--database", os.path.join(utils.TESTDATA, "simple_database.csv"),
        "--config", os.path.join(utils.TESTDATA, "server_open.conf"),
        "--no-limit",
        "--no-dry-run",
    )

    # Mock smtp object with function calls recorded
    smtp = mock_SMTP.return_value
    assert smtp.sendmail.call_count == 1


@mock.patch('smtplib.SMTP')
def test_utf8_database(mock_SMTP):
    """Verify UTF8 support when template is rendered with UTF-8 value."""
    mailmerge.api.sendall(
        database_path=os.path.join(utils.TESTDATA, "utf8_database.csv"),
        template_path=os.path.join(utils.TESTDATA, "simple_template.txt"),
        config_path=os.path.join(utils.TESTDATA, "server_open.conf"),
        limit=1,
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

    # Verify message encoding.  The template was ASCII, but when the template
    # is rendered with UTF-8 data, the result is UTF-8 encoding.
    assert message.get_content_maintype() == "text"
    assert message.get_content_subtype() == "plain"
    assert message.get_content_charset() == "utf-8"

    # Verify content
    # NOTE: to decode a base46-encoded string:
    # print((str(base64.b64decode(payload), "utf-8")))
    payload = message.get_payload()
    payload = message.get_payload().replace("\n", "")
    assert payload == 'SGksIExhyJ1hbW9uLAoKWW91ciBudW1iZXIgaXMgMTcu'


def test_enumerate_limit_no_limit():
    """Verify limit=-1 results in no early termination."""
    iterations = 0
    for _, _ in mailmerge.api.enumerate_limit(["a", "b", "c"], -1):
        iterations += 1
    assert iterations == 3


def test_enumerate_limit_values():
    """Verify limit=-1 results in no early termination."""
    values = ["a", "b", "c"]
    for i, a in mailmerge.api.enumerate_limit(values, -1):
        assert a == values[i]


def test_enumerate_limit_stop_early():
    """Verify limit results in early termination."""
    iterations = 0
    for _, _ in mailmerge.api.enumerate_limit(["a", "b", "c"], 2):
        iterations += 1
    assert iterations == 2


def test_enumerate_limit_zero():
    """Verify limit results in early termination."""
    iterations = 0
    for _, _ in mailmerge.api.enumerate_limit(["a", "b", "c"], 0):
        iterations += 1
    assert iterations == 0

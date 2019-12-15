"""
System tests.

Andrew DeOrio <awdeorio@umich.edu>
"""
import re
import sh
from . import utils

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path


def test_stdout():
    """Verify stdout and stderr with dry run on simple input files."""
    mailmerge_cmd = sh.Command("mailmerge")
    output = mailmerge_cmd(
        "--template", utils.TESTDATA/"simple_template.txt",
        "--database", utils.TESTDATA/"simple_database.csv",
        "--config", utils.TESTDATA/"server_open.conf",
        "--no-limit",
        "--dry-run",
    )

    # Verify mailmerge output.  We'll filter out the Date header because it
    # won't match exactly.
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")
    assert stderr == ""
    assert "Date:" in stdout
    stdout = re.sub(r"Date.*\n", "", stdout)
    assert stdout == """>>> message 0
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Hi, Myself,

Your number is 17.
>>> sent message 0
>>> message 1
TO: bob@bobdomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Hi, Bob,

Your number is 42.
>>> sent message 1
>>> This was a dry run.  To send messages, use the --no-dry-run option.
"""


def test_no_options(tmpdir):
    """Verify help message when called with no options.

    Run mailmerge at the CLI with no options.  Do this in an empty temporary
    directory to ensure that mailmerge doesn't find any default input files.

    pytest tmpdir docs:
    http://doc.pytest.org/en/latest/tmpdir.html#the-tmpdir-fixture

    sh _ok_code docs
    https://amoffat.github.io/sh/sections/special_arguments.html#ok-code
    """
    mailmerge = sh.Command("mailmerge")
    with tmpdir.as_cwd():
        output = mailmerge(_ok_code=1)  # expect non-zero exit
    assert "Error: can't find template email mailmerge_template.txt" in output
    assert "https://github.com/awdeorio/mailmerge" in output


def test_sample(tmpdir):
    """Verify --sample."""
    mailmerge = sh.Command("mailmerge")

    # Run `mailmerge --sample`
    with tmpdir.as_cwd():
        output = mailmerge("--sample")

    # Verify file were created
    assert Path("mailmerge_template.txt").exists()
    assert Path("mailmerge_database.csv").exists()
    assert Path("mailmerge_server.conf").exists()

    # Run `mailmerge`, which should dry-run sending one message
    with tmpdir.as_cwd():
        output = mailmerge()
    assert "sent message 0" in output
    assert "Limit was 1 messages" in output
    assert "This was a dry run" in output

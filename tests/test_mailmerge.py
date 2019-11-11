"""
System tests.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
import re
import sh
from . import utils


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

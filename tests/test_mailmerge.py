"""
System tests.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
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

    # Verify mailmerge output
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")
    assert stderr == ""
    assert ">>> message 0" in stdout
    assert ">>> sent message 0" in stdout
    assert ">>> message 1" in stdout
    assert ">>> sent message 1" in stdout

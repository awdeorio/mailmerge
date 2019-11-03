"""Tests for utility functions."""
import os
import sh
import utils
import mailmerge.utils


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


def test_enumerate_limit_no_limit():
    """Verify limit=-1 results in no early termination."""
    iterations = 0
    for _, _ in mailmerge.utils.enumerate_limit(["a", "b", "c"], -1):
        iterations += 1
    assert iterations == 3


def test_enumerate_limit_values():
    """Verify limit=-1 results in no early termination."""
    values = ["a", "b", "c"]
    for i, value in mailmerge.utils.enumerate_limit(values, -1):
        assert value == values[i]


def test_enumerate_limit_stop_early():
    """Verify limit results in early termination."""
    iterations = 0
    for _, _ in mailmerge.utils.enumerate_limit(["a", "b", "c"], 2):
        iterations += 1
    assert iterations == 2


def test_enumerate_limit_zero():
    """Verify limit results in early termination."""
    iterations = 0
    for _, _ in mailmerge.utils.enumerate_limit(["a", "b", "c"], 0):
        iterations += 1
    assert iterations == 0

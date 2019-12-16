"""
System tests.

Andrew DeOrio <awdeorio@umich.edu>
"""
import re
import sh
import pytest
from . import utils

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

# The sh library triggers lot of false no-member errors
# pylint: disable=no-member


def test_stdout():
    """Verify stdout and stderr with dry run on simple input files."""
    output = sh.mailmerge(
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
    with tmpdir.as_cwd():
        output = sh.mailmerge(_ok_code=1)  # expect non-zero exit
    assert "Error: can't find template email mailmerge_template.txt" in output
    assert "https://github.com/awdeorio/mailmerge" in output


def test_sample(tmpdir):
    """Verify --sample creates sample input files."""
    with tmpdir.as_cwd():
        sh.mailmerge("--sample")
    assert Path("mailmerge_template.txt").exists()
    assert Path("mailmerge_database.csv").exists()
    assert Path("mailmerge_server.conf").exists()


def test_sample_clobber_template(tmpdir):
    """Verify --sample won't clobber template if it already exists."""
    with tmpdir.as_cwd():
        Path("mailmerge_template.txt").touch()
        with pytest.raises(sh.ErrorReturnCode_1):
            sh.mailmerge("--sample")


def test_sample_clobber_database(tmpdir):
    """Verify --sample won't clobber database if it already exists."""
    with tmpdir.as_cwd():
        Path("mailmerge_database.csv").touch()
        with pytest.raises(sh.ErrorReturnCode_1):
            sh.mailmerge("--sample")


def test_sample_clobber_config(tmpdir):
    """Verify --sample won't clobber config if it already exists."""
    with tmpdir.as_cwd():
        Path("mailmerge_server.conf").touch()
        with pytest.raises(sh.ErrorReturnCode_1):
            sh.mailmerge("--sample")


def test_defaults(tmpdir):
    """When no options are provided, use default input file names."""
    with tmpdir.as_cwd():
        sh.mailmerge("--sample")
        output = sh.mailmerge()
    assert "sent message 0" in output
    assert "Limit was 1 messages" in output
    assert "This was a dry run" in output


def test_dry_run():
    """Verify --dry-run output."""
    output = sh.mailmerge(
        "--template", utils.TESTDATA/"simple_template.txt",
        "--database", utils.TESTDATA/"simple_database.csv",
        "--config", utils.TESTDATA/"server_ssl.conf",
        "--dry-run",
    )
    assert "Your number is 17." in output
    assert "sent message 0" in output
    assert "Limit was 1 messages" in output
    assert "This was a dry run" in output


def test_bad_limit():
    """Verify --limit with bad value."""
    with pytest.raises(sh.ErrorReturnCode_1):
        sh.mailmerge(
            "--template", utils.TESTDATA/"simple_template.txt",
            "--database", utils.TESTDATA/"simple_database.csv",
            "--config", utils.TESTDATA/"server_open.conf",
            "--dry-run",
            "--limit", "-1",
        )


def test_limit_combo():
    """TVerify --limit 1 --no-limit results in no limit."""
    output = sh.mailmerge(
        "--template", utils.TESTDATA/"simple_template.txt",
        "--database", utils.TESTDATA/"simple_database.csv",
        "--config", utils.TESTDATA/"server_open.conf",
        "--dry-run",
        "--no-limit",
        "--limit", "1",
    )
    assert "sent message 0" in output
    assert "sent message 1" in output
    assert "Limit was 1" not in output


def test_file_not_found(tmpdir):
    """Verify error when input file not found."""
    with tmpdir.as_cwd():
        with pytest.raises(sh.ErrorReturnCode_1):
            sh.mailmerge("--template", "notfound.txt")
        with pytest.raises(sh.ErrorReturnCode_1):
            sh.mailmerge("--database", "notfound.csv")
        with pytest.raises(sh.ErrorReturnCode_1):
            sh.mailmerge("--config", "notfound.conf")


def test_help():
    """Verify -h or --help produces a help message."""
    output = sh.mailmerge("--help")
    assert "Usage:" in output
    assert "Options:" in output
    output2 = sh.mailmerge("-h")  # Short option is an alias
    assert output == output2


def test_version():
    """Verify --version produces a version."""
    output = sh.mailmerge("--version")
    assert "mailmerge, version" in output


def test_bad_template(tmp_path):
    """Template containing jinja error should produce an error."""
    template_path = tmp_path / "template.txt"
    template_path.write_text("TO: {{error_not_in_database}}")
    with pytest.raises(sh.ErrorReturnCode_1):
        sh.mailmerge("--template", template_path)

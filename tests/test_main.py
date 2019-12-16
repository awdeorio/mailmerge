"""
System tests.

Andrew DeOrio <awdeorio@umich.edu>
"""
import re
import textwrap
import sh
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
    assert output.stderr.decode("utf-8") == ""
    assert "Error: can't find template mailmerge_template.txt" in output
    assert "https://github.com/awdeorio/mailmerge" in output


def test_sample(tmpdir):
    """Verify --sample creates sample input files."""
    with tmpdir.as_cwd():
        output = sh.mailmerge("--sample")
        assert Path("mailmerge_template.txt").exists()
        assert Path("mailmerge_database.csv").exists()
        assert Path("mailmerge_server.conf").exists()
    assert output.stderr.decode("utf-8") == ""
    assert "Creating sample template" in output
    assert "Creating sample database" in output
    assert "Creating sample config" in output


def test_sample_clobber_template(tmpdir):
    """Verify --sample won't clobber template if it already exists."""
    with tmpdir.as_cwd():
        Path("mailmerge_template.txt").touch()
        output = sh.mailmerge("--sample", _ok_code=1)
    assert output.stderr.decode("utf-8") == ""
    assert "Error: file exists" in output


def test_sample_clobber_database(tmpdir):
    """Verify --sample won't clobber database if it already exists."""
    with tmpdir.as_cwd():
        Path("mailmerge_database.csv").touch()
        output = sh.mailmerge("--sample", _ok_code=1)
    assert output.stderr.decode("utf-8") == ""
    assert "Error: file exists" in output


def test_sample_clobber_config(tmpdir):
    """Verify --sample won't clobber config if it already exists."""
    with tmpdir.as_cwd():
        Path("mailmerge_server.conf").touch()
        output = sh.mailmerge("--sample", _ok_code=1)
    assert output.stderr.decode("utf-8") == ""
    assert "Error: file exists" in output


def test_defaults(tmpdir):
    """When no options are provided, use default input file names."""
    with tmpdir.as_cwd():
        sh.mailmerge("--sample")
        output = sh.mailmerge()
    assert output.stderr.decode("utf-8") == ""
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
    assert output.stderr.decode("utf-8") == ""
    assert "Your number is 17." in output
    assert "sent message 0" in output
    assert "Limit was 1 messages" in output
    assert "This was a dry run" in output


def test_bad_limit():
    """Verify --limit with bad value."""
    output = sh.mailmerge(
        "--template", utils.TESTDATA/"simple_template.txt",
        "--database", utils.TESTDATA/"simple_database.csv",
        "--config", utils.TESTDATA/"server_open.conf",
        "--dry-run",
        "--limit", "-1",
        _ok_code=2,
    )
    assert "Error: Invalid value" in output.stderr.decode("utf-8")


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
    assert output.stderr.decode("utf-8") == ""
    assert "sent message 0" in output
    assert "sent message 1" in output
    assert "Limit was 1" not in output


def test_template_not_found(tmpdir):
    """Verify error when template input file not found."""
    with tmpdir.as_cwd():
        output = sh.mailmerge("--template", "notfound.txt", _ok_code=1)
    assert output.stderr.decode("utf-8") == ""
    assert "Error: can't find template" in output


def test_database_not_found(tmpdir):
    """Verify error when database input file not found."""
    with tmpdir.as_cwd():
        Path("mailmerge_template.txt").touch()
        output = sh.mailmerge("--database", "notfound.csv", _ok_code=1)
    assert output.stderr.decode("utf-8") == ""
    assert "Error: can't find database" in output


def test_config_not_found(tmpdir):
    """Verify error when config input file not found."""
    with tmpdir.as_cwd():
        Path("mailmerge_template.txt").touch()
        Path("mailmerge_database.csv").touch()
        output = sh.mailmerge("--config", "notfound.conf", _ok_code=1)
    assert output.stderr.decode("utf-8") == ""
    assert "Error: can't find config" in output


def test_help():
    """Verify -h or --help produces a help message."""
    output = sh.mailmerge("--help")
    assert output.stderr.decode("utf-8") == ""
    assert "Usage:" in output
    assert "Options:" in output
    output2 = sh.mailmerge("-h")  # Short option is an alias
    assert output2.stderr.decode("utf-8") == ""
    assert output == output2


def test_version():
    """Verify --version produces a version."""
    output = sh.mailmerge("--version")
    assert output.stderr.decode("utf-8") == ""
    assert "mailmerge, version" in output


def test_bad_template(tmpdir):
    """Template containing jinja error should produce an error."""
    template_path = Path(tmpdir/"template.txt")

    # Template has a bad key
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{error_not_in_database}}
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hi {{name}},
    """))

    # Normal database
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email,name
        to@test.com,Bob
    """))

    # Normal, unsecure server config
    config_path = Path(tmpdir/"config.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        security = Never
    """))

    # Run mailmerge, which should exit 1
    output = sh.mailmerge(
        "--template", template_path,
        "--database", database_path,
        "--config", config_path,
        _ok_code=1,
    )

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert "Error in Jinja2 template" in output
    assert "error_not_in_database" in output


def test_bad_database(tmpdir):
    """Database mismatch with jinja variables should produce an error."""
    # Normal template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hi {{name}},
    """))

    # Database is header doesn't match template
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        error_not_in_template,name
        to1@test.com,Bob
    """))

    # Normal, unsecure server config
    config_path = Path(tmpdir/"config.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
        security = Never
    """))

    # Run mailmerge, which should exit 1
    output = sh.mailmerge(
        "--template", template_path,
        "--database", database_path,
        "--config", config_path,
        _ok_code=1,
    )

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert "Error in Jinja2 template" in output
    assert "email" in output  # this is the missing key in the database


def test_bad_config(tmpdir):
    """Config containing an error should produce an error."""
    # Normal template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hi {{name}},
    """))

    # Normal database
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email,name
        to@test.com,Bob
    """))

    # Server config is missing host
    config_path = Path(tmpdir/"config.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        port = 25
        security = Never
    """))

    # Run mailmerge, which should exit 1
    output = sh.mailmerge(
        "--template", template_path,
        "--database", database_path,
        "--config", config_path,
        _ok_code=1,
    )

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert "Error reading config file" in output

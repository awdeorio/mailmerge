"""
System tests.

Andrew DeOrio <awdeorio@umich.edu>

pytest tmpdir docs:
http://doc.pytest.org/en/latest/tmpdir.html#the-tmpdir-fixture
"""
import copy
import shutil
import re
from pathlib import Path
import textwrap
import click.testing
from mailmerge.__main__ import main
from . import utils


def test_no_options(tmpdir):
    """Verify help message when called with no options.

    Run mailmerge at the CLI with no options.  Do this in an empty temporary
    directory to ensure that mailmerge doesn't find any default input files.
    """
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, [])
    assert result.exit_code == 1
    assert 'Error: can\'t find template "mailmerge_template.txt"' in \
        result.output
    assert "https://github.com/awdeorio/mailmerge" in result.output


def test_sample(tmpdir):
    """Verify --sample creates sample input files."""
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--sample"])
    assert not result.exception
    assert result.exit_code == 0
    assert Path(tmpdir/"mailmerge_template.txt").exists()
    assert Path(tmpdir/"mailmerge_database.csv").exists()
    assert Path(tmpdir/"mailmerge_server.conf").exists()
    assert "Created sample template" in result.output
    assert "Created sample database" in result.output
    assert "Created sample config" in result.output


def test_sample_clobber_template(tmpdir):
    """Verify --sample won't clobber template if it already exists."""
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        Path("mailmerge_template.txt").touch()
        result = runner.invoke(main, ["--sample"])
    assert result.exit_code == 1
    assert "Error: file exists: mailmerge_template.txt" in result.output


def test_sample_clobber_database(tmpdir):
    """Verify --sample won't clobber database if it already exists."""
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        Path("mailmerge_database.csv").touch()
        result = runner.invoke(main, ["--sample"])
    assert result.exit_code == 1
    assert "Error: file exists: mailmerge_database.csv" in result.output


def test_sample_clobber_config(tmpdir):
    """Verify --sample won't clobber config if it already exists."""
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        Path("mailmerge_server.conf").touch()
        result = runner.invoke(main, ["--sample"])
    assert result.exit_code == 1
    assert "Error: file exists: mailmerge_server.conf" in result.output


def test_defaults(tmpdir):
    """When no options are provided, use default input file names."""
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--sample"])
    assert not result.exception
    assert result.exit_code == 0
    with tmpdir.as_cwd():
        result = runner.invoke(main, [])
    assert not result.exception
    assert result.exit_code == 0
    assert "message 1 sent" in result.output
    assert "Limit was 1 message" in result.output
    assert "This was a dry run" in result.output


def test_bad_limit(tmpdir):
    """Verify --limit with bad value."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: from@test.com

        Hello world
    """), encoding="utf8")

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email
        one@test.com
        two@test.com
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--dry-run", "--limit", "-1"])
    assert result.exit_code == 2
    assert "Error: Invalid value" in result.output


def test_limit_combo(tmpdir):
    """Verify --limit 1 --no-limit results in no limit."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: from@test.com

        Hello world
    """), encoding="utf8")

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email
        one@test.com
        two@test.com
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--no-limit", "--limit", "1"])
    assert not result.exception
    assert result.exit_code == 0
    assert "message 1 sent" in result.output
    assert "message 2 sent" in result.output
    assert "Limit was 1" not in result.output


def test_template_not_found(tmpdir):
    """Verify error when template input file not found."""
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--template", "notfound.txt"])
    assert result.exit_code == 1
    assert "Error: can't find template" in result.output


def test_database_not_found(tmpdir):
    """Verify error when database input file not found."""
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        Path("mailmerge_template.txt").touch()
        result = runner.invoke(main, ["--database", "notfound.csv"])
    assert result.exit_code == 1
    assert "Error: can't find database" in result.output


def test_config_not_found(tmpdir):
    """Verify error when config input file not found."""
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        Path("mailmerge_template.txt").touch()
        Path("mailmerge_database.csv").touch()
        result = runner.invoke(main, ["--config", "notfound.conf"])
    assert result.exit_code == 1
    assert "Error: can't find config" in result.output


def test_help():
    """Verify -h or --help produces a help message."""
    runner = click.testing.CliRunner()
    result1 = runner.invoke(main, ["--help"])
    assert result1.exit_code == 0
    assert "Usage:" in result1.stdout
    assert "Options:" in result1.stdout
    result2 = runner.invoke(main, ["-h"])  # Short option is an alias
    assert result1.stdout == result2.stdout


def test_version():
    """Verify --version produces a version."""
    runner = click.testing.CliRunner()
    result = runner.invoke(main, ["--version"])
    assert not result.exception
    assert result.exit_code == 0
    assert "version" in result.output


def test_bad_template(tmpdir):
    """Template mismatch with database header should produce an error."""
    # Template has a bad key
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{error_not_in_database}}
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hello world
    """), encoding="utf8")

    # Normal database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email
        to@test.com
    """), encoding="utf8")

    # Normal, unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge, which should exit 1
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, [])
    assert result.exit_code == 1

    # Verify output
    assert "template.txt: 'error_not_in_database' is undefined" in \
        result.output


def test_bad_database(tmpdir):
    """Database read error should produce a sane error."""
    # Normal template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """), encoding="utf8")

    # Database with unmatched quote
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        message
        "hello world
    """), encoding="utf8")

    # Normal, unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge, which should exit 1
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, [])
    assert result.exit_code == 1

    # Verify output
    assert "database.csv:1: unexpected end of data" in result.output


def test_bad_config(tmpdir):
    """Config containing an error should produce an error."""
    # Normal template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
    """), encoding="utf8")

    # Normal database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        dummy
        asdf
    """), encoding="utf8")

    # Server config is missing host
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        port = 25
    """), encoding="utf8")

    # Run mailmerge, which should exit 1
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, [])
    assert result.exit_code == 1

    # Verify output
    assert "server.conf: No option 'host' in section: 'smtp_server'" in \
        result.output


def test_attachment(tmpdir):
    """Verify attachments feature output."""
    # First attachment
    attachment1_path = Path(tmpdir/"attachment1.txt")
    attachment1_path.write_text("Hello world\n", encoding="utf8")

    # Second attachment
    attachment2_path = Path(tmpdir/"attachment2.txt")
    attachment2_path.write_text("Hello mailmerge\n", encoding="utf8")

    # Template with attachment header
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: from@test.com
        ATTACHMENT: attachment1.txt
        ATTACHMENT: attachment2.txt

        Hello world
    """), encoding="utf8")

    # Simple database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email
        to@test.com
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "text"])
    assert not result.exception
    assert result.exit_code == 0

    # Verify output
    assert ">>> message part: text/plain" in result.output
    assert "Hello world" in result.output  # message
    assert ">>> message part: attachment attachment1.txt" in result.output
    assert ">>> message part: attachment attachment2.txt" in result.output


def test_utf8_template(tmpdir):
    """Message is utf-8 encoded when only the template contains utf-8 chars."""
    # Template with UTF-8 characters and emoji
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: from@test.com

        Laȝamon 😀 klâwen
    """), encoding="utf8")

    # Simple database without utf-8 characters
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email
        to@test.com
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    result = runner.invoke(main, [
        "--template", template_path,
        "--database", database_path,
        "--config", config_path,
        "--dry-run",
        "--output-format", "text",
    ])
    assert not result.exception
    assert result.exit_code == 0

    # Remove the Date string, which will be different each time
    stdout = copy.deepcopy(result.output)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert stdout == textwrap.dedent("""\
        >>> message 1
        TO: to@test.com
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: text/plain; charset="utf-8"
        Content-Transfer-Encoding: base64
        Date: REDACTED

        Laȝamon 😀 klâwen

        >>> message 1 sent
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)  # noqa: E501


def test_utf8_database(tmpdir):
    """Message is utf-8 encoded when only the databse contains utf-8 chars."""
    # Simple template without UTF-8 characters
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """), encoding="utf8")

    # Database with utf-8 characters and emoji
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        message
        Laȝamon 😀 klâwen
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "text"])
    assert not result.exception
    assert result.exit_code == 0

    # Remove the Date string, which will be different each time
    stdout = copy.deepcopy(result.output)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert stdout == textwrap.dedent("""\
        >>> message 1
        TO: to@test.com
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: text/plain; charset="utf-8"
        Content-Transfer-Encoding: base64
        Date: REDACTED

        Laȝamon 😀 klâwen

        >>> message 1 sent
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)  # noqa: E501


def test_utf8_headers(tmpdir):
    """Message is utf-8 encoded when headers contain utf-8 chars."""
    # Template with UTF-8 characters and emoji in headers
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: Laȝamon <to@test.com>
        FROM: klâwen <from@test.com>
        SUBJECT: Laȝamon 😀 klâwen

        {{message}}
    """), encoding="utf8")

    # Simple database without utf-8 characters
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        message
        hello
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, [
            "--template", template_path,
            "--database", database_path,
            "--config", config_path,
            "--dry-run",
            "--output-format", "raw",
        ])
    assert not result.exception
    assert result.exit_code == 0

    # Remove the Date string, which will be different each time
    stdout = copy.deepcopy(result.output)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert stdout == textwrap.dedent("""\
        >>> message 1
        TO: =?utf-8?b?TGHInWFtb24gPHRvQHRlc3QuY29tPg==?=
        FROM: =?utf-8?b?a2zDondlbiA8ZnJvbUB0ZXN0LmNvbT4=?=
        SUBJECT: =?utf-8?b?TGHInWFtb24g8J+YgCBrbMOid2Vu?=
        MIME-Version: 1.0
        Content-Type: text/plain; charset="utf-8"
        Content-Transfer-Encoding: base64
        Date: REDACTED

        aGVsbG8=

        >>> message 1 sent
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)  # noqa: E501


def test_resume(tmpdir):
    """Verify --resume option starts "in the middle" of the database."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """), encoding="utf8")

    # Database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        message
        hello
        world
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--resume", "2", "--no-limit"])
    assert not result.exception
    assert result.exit_code == 0

    # Verify only second message was sent
    assert "hello" not in result.output
    assert "message 1 sent" not in result.output
    assert "world" in result.output
    assert "message 2 sent" in result.output


def test_resume_too_small(tmpdir):
    """Verify --resume <= 0 prints an error message."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """), encoding="utf8")

    # Database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        message
        hello
        world
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run "mailmerge --resume 0" and check output
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--resume", "0"])
    assert result.exit_code == 2
    assert "Invalid value" in result.output

    # Run "mailmerge --resume -1" and check output
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--resume", "-1"])
    assert result.exit_code == 2
    assert "Invalid value" in result.output


def test_resume_too_big(tmpdir):
    """Verify --resume > database does nothing."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """), encoding="utf8")

    # Database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        message
        hello
        world
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run and check output
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--resume", "3", "--no-limit"])
    assert not result.exception
    assert result.exit_code == 0
    assert "sent message" not in result.output


def test_resume_hint_on_config_error(tmpdir):
    """Verify *no* --resume hint when error is after first message."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """), encoding="utf8")

    # Database with error on second entry
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        message
        hello
        "world
    """), encoding="utf8")

    # Server config missing port
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
    """), encoding="utf8")

    # Run and check output
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, [])
    assert result.exit_code == 1
    assert "--resume 1" not in result.output


def test_resume_hint_on_csv_error(tmpdir):
    """Verify --resume hint after CSV error."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """), encoding="utf8")

    # Database with unmatched quote on second entry
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        message
        hello
        "world
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run and check output
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--resume", "2", "--no-limit"])
    assert result.exit_code == 1
    assert "--resume 2" in result.output


def test_other_mime_type(tmpdir):
    """Verify output with a MIME type that's not text or an attachment."""
    # Template containing a pdf
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"

        --boundary
        Content-Type: text/plain; charset=us-ascii

        Hello world

        --boundary
        Content-Type: application/pdf

        DUMMY
    """), encoding="utf8")

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email
        one@test.com
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, [])
    assert not result.exception
    assert result.exit_code == 0

    # Verify output
    stdout = copy.deepcopy(result.output)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)
    assert stdout == textwrap.dedent("""\
        \x1b[7m\x1b[1m\x1b[36m>>> message 1\x1b(B\x1b[m
        TO: one@test.com
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"
        Date: REDACTED

        \x1b[36m>>> message part: text/plain\x1b(B\x1b[m
        Hello world


        \x1b[36m>>> message part: application/pdf\x1b(B\x1b[m
        \x1b[7m\x1b[1m\x1b[36m>>> message 1 sent\x1b(B\x1b[m
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)  # noqa: E501


def test_database_bom(tmpdir):
    """Bug fix CSV with a byte order mark (BOM).

    It looks like Excel will sometimes save a file with Byte Order Mark
    (BOM). When the mailmerge database contains a BOM, it can't seem to find
    the first header key.
    https://github.com/awdeorio/mailmerge/issues/93

    """
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: My Self <myself@mydomain.com>

        Hello {{name}}
    """), encoding="utf8")

    # Copy database containing a BOM
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_with_bom = utils.TESTDATA/"mailmerge_database_with_BOM.csv"
    shutil.copyfile(database_with_bom, database_path)

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "text"])
    assert not result.exception
    assert result.exit_code == 0

    # Verify output
    stdout = copy.deepcopy(result.output)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)
    assert stdout == textwrap.dedent("""\
        >>> message 1
        TO: to@test.com
        FROM: My Self <myself@mydomain.com>
        MIME-Version: 1.0
        Content-Type: text/plain; charset="us-ascii"
        Content-Transfer-Encoding: 7bit
        Date: REDACTED

        Hello My Name

        >>> message 1 sent
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)  # noqa: E501


def test_database_tsv(tmpdir):
    """Automatically detect TSV database format."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: My Self <myself@mydomain.com>

        Hello {{name}}
    """), encoding="utf8")

    # Tab-separated format database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email\tname
        to@test.com\tMy Name
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "text"])
    assert not result.exception
    assert result.exit_code == 0

    # Verify output
    stdout = copy.deepcopy(result.output)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)
    assert stdout == textwrap.dedent("""\
        >>> message 1
        TO: to@test.com
        FROM: My Self <myself@mydomain.com>
        MIME-Version: 1.0
        Content-Type: text/plain; charset="us-ascii"
        Content-Transfer-Encoding: 7bit
        Date: REDACTED

        Hello My Name

        >>> message 1 sent
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)  # noqa: E501


def test_database_semicolon(tmpdir):
    """Automatically detect semicolon-delimited database format."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: My Self <myself@mydomain.com>

        Hello {{name}}
    """), encoding="utf8")

    # Semicolon-separated format database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email;name
        to@test.com;My Name
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "text"])
    assert not result.exception
    assert result.exit_code == 0

    # Verify output
    stdout = copy.deepcopy(result.output)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)
    assert stdout == textwrap.dedent("""\
        >>> message 1
        TO: to@test.com
        FROM: My Self <myself@mydomain.com>
        MIME-Version: 1.0
        Content-Type: text/plain; charset="us-ascii"
        Content-Transfer-Encoding: 7bit
        Date: REDACTED

        Hello My Name

        >>> message 1 sent
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)  # noqa: E501

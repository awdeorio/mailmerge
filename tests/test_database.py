"""
System tests focused on database.

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


def test_database_not_found(tmpdir):
    """Verify error when database input file not found."""
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        Path("mailmerge_template.txt").touch()
        result = runner.invoke(main, ["--database", "notfound.csv"])
    assert result.exit_code == 1
    assert "Error: can't find database" in result.output

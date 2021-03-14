# coding=utf-8
# Python 2 source containing unicode https://www.python.org/dev/peps/pep-0263/
"""
System tests.

Andrew DeOrio <awdeorio@umich.edu>

pytest tmpdir docs:
http://doc.pytest.org/en/latest/tmpdir.html#the-tmpdir-fixture
"""
import re
import textwrap
import sh
import pytest

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

# The sh library triggers lot of false no-member errors
# pylint: disable=no-member


def test_no_options(tmpdir):
    """Verify help message when called with no options.

    Run mailmerge at the CLI with no options.  Do this in an empty temporary
    directory to ensure that mailmerge doesn't find any default input files.
    """
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        sh.mailmerge()
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert 'Error: can\'t find template "mailmerge_template.txt"' in stderr
    assert "https://github.com/awdeorio/mailmerge" in stderr


def test_sample(tmpdir):
    """Verify --sample creates sample input files."""
    with tmpdir.as_cwd():
        output = sh.mailmerge("--sample")
    assert Path(tmpdir/"mailmerge_template.txt").exists()
    assert Path(tmpdir/"mailmerge_database.csv").exists()
    assert Path(tmpdir/"mailmerge_server.conf").exists()
    assert output.stderr.decode("utf-8") == ""
    assert "Created sample template" in output
    assert "Created sample database" in output
    assert "Created sample config" in output


def test_sample_clobber_template(tmpdir):
    """Verify --sample won't clobber template if it already exists."""
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        Path("mailmerge_template.txt").touch()
        sh.mailmerge("--sample")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "Error: file exists: mailmerge_template.txt" in stderr


def test_sample_clobber_database(tmpdir):
    """Verify --sample won't clobber database if it already exists."""
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        Path("mailmerge_database.csv").touch()
        sh.mailmerge("--sample")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "Error: file exists: mailmerge_database.csv" in stderr


def test_sample_clobber_config(tmpdir):
    """Verify --sample won't clobber config if it already exists."""
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        Path("mailmerge_server.conf").touch()
        sh.mailmerge("--sample")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "Error: file exists: mailmerge_server.conf" in stderr


def test_defaults(tmpdir):
    """When no options are provided, use default input file names."""
    with tmpdir.as_cwd():
        sh.mailmerge("--sample")
        output = sh.mailmerge()
    assert output.stderr.decode("utf-8") == ""
    assert "message 1 sent" in output
    assert "Limit was 1 message" in output
    assert "This was a dry run" in output


def test_bad_limit(tmpdir):
    """Verify --limit with bad value."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Hello world
    """))

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        one@test.com
        two@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_2) as error:
        sh.mailmerge("--dry-run", "--limit", "-1")
    stderr = error.value.stderr.decode("utf-8")
    assert "Error: Invalid value" in stderr


def test_limit_combo(tmpdir):
    """Verify --limit 1 --no-limit results in no limit."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Hello world
    """))

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        one@test.com
        two@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge
    with tmpdir.as_cwd():
        output = sh.mailmerge("--no-limit", "--limit", "1")
    assert output.stderr.decode("utf-8") == ""
    assert "message 1 sent" in output
    assert "message 2 sent" in output
    assert "Limit was 1" not in output


def test_template_not_found(tmpdir):
    """Verify error when template input file not found."""
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        sh.mailmerge("--template", "notfound.txt")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "Error: can't find template" in stderr


def test_database_not_found(tmpdir):
    """Verify error when database input file not found."""
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        Path("mailmerge_template.txt").touch()
        sh.mailmerge("--database", "notfound.csv")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "Error: can't find database" in stderr


def test_config_not_found(tmpdir):
    """Verify error when config input file not found."""
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        Path("mailmerge_template.txt").touch()
        Path("mailmerge_database.csv").touch()
        sh.mailmerge("--config", "notfound.conf")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "Error: can't find config" in stderr


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
    """Template mismatch with database header should produce an error."""
    # Template has a bad key
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{error_not_in_database}}
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hello world
    """))

    # Normal database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        to@test.com
    """))

    # Normal, unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge, which should exit 1
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        sh.mailmerge()

    # Verify output
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "template.txt: 'error_not_in_database' is undefined" in stderr


def test_bad_database(tmpdir):
    """Database read error should produce a sane error."""
    # Normal template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Database with unmatched quote
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        "hello world
    """))

    # Normal, unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge, which should exit 1
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        sh.mailmerge()

    # Verify output
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "database.csv:1: unexpected end of data" in stderr


def test_bad_config(tmpdir):
    """Config containing an error should produce an error."""
    # Normal template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
    """))

    # Normal database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        dummy
        asdf
    """))

    # Server config is missing host
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        port = 25
    """))

    # Run mailmerge, which should exit 1
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        sh.mailmerge()
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")

    # Verify output
    assert stdout == ""
    assert "server.conf: No option 'host' in section: 'smtp_server'" in stderr


def test_attachment(tmpdir):
    """Verify attachments feature output."""
    # First attachment
    attachment1_path = Path(tmpdir/"attachment1.txt")
    attachment1_path.write_text(u"Hello world\n")

    # Second attachment
    attachment2_path = Path(tmpdir/"attachment2.txt")
    attachment2_path.write_text(u"Hello mailmerge\n")

    # Template with attachment header
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com
        ATTACHMENT: attachment1.txt
        ATTACHMENT: attachment2.txt

        Hello world
    """))

    # Simple database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        to@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge
    with tmpdir.as_cwd():
        output = sh.mailmerge("--output-format", "text")

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert ">>> message part: text/plain" in output
    assert "Hello world" in output  # message
    assert ">>> message part: attachment attachment1.txt" in output
    assert ">>> message part: attachment attachment2.txt" in output


def test_utf8_template(tmpdir):
    """Message is utf-8 encoded when only the template contains utf-8 chars."""
    # Template with UTF-8 characters and emoji
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Laȝamon 😀 klâwen
    """))

    # Simple database without utf-8 characters
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        to@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge
    output = sh.mailmerge(
        "--template", template_path,
        "--database", database_path,
        "--config", config_path,
        "--dry-run",
        "--output-format", "text",
    )

    # Remove the Date string, which will be different each time
    stdout = output.stdout.decode("utf-8")
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert stdout == textwrap.dedent(u"""\
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
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Database with utf-8 characters and emoji
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        Laȝamon 😀 klâwen
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge
    with tmpdir.as_cwd():
        output = sh.mailmerge("--output-format", "text")

    # Remove the Date string, which will be different each time
    stdout = output.stdout.decode("utf-8")
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert stdout == textwrap.dedent(u"""\
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
    template_path.write_text(textwrap.dedent(u"""\
        TO: Laȝamon <to@test.com>
        FROM: klâwen <from@test.com>
        SUBJECT: Laȝamon 😀 klâwen

        {{message}}
    """))

    # Simple database without utf-8 characters
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        hello
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge
    output = sh.mailmerge(
        "--template", template_path,
        "--database", database_path,
        "--config", config_path,
        "--dry-run",
        "--output-format", "raw",
    )

    # Remove the Date string, which will be different each time
    stdout = output.stdout.decode("utf-8")
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert stdout == textwrap.dedent(u"""\
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


def test_complicated(tmpdir):
    """Complicated end-to-end test.

    Includes templating, TO, CC, BCC, UTF8 characters, emoji, attachments,
    encoding mismatch (header is us-ascii, characters used are utf-8).  Also,
    multipart message in plaintext and HTML.
    """
    # First attachment
    attachment1_path = Path(tmpdir/"attachment1.txt")
    attachment1_path.write_text(u"Hello world\n")

    # Second attachment
    attachment2_path = Path(tmpdir/"attachment2.csv")
    attachment2_path.write_text(u"hello,mailmerge\n")

    # Template with attachment header
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com
        CC: cc1@test.com, cc2@test.com
        BCC: bcc1@test.com, bcc2@test.com
        ATTACHMENT: attachment1.txt
        ATTACHMENT: attachment2.csv
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"

        This is a MIME-encoded message. If you are seeing this, your mail
        reader is old.

        --boundary
        Content-Type: text/plain; charset=us-ascii

        {{message}}


        --boundary
        Content-Type: text/html; charset=us-ascii

        <html>
          <body>
            <p>{{message}}</p>
          </body>
        </html>


    """))

    # Database with utf-8, emoji, quotes, and commas.  Note that quotes are
    # escaped with double quotes, not backslash.
    # https://docs.python.org/3.7/library/csv.html#csv.Dialect.doublequote
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u'''\
        email,message
        one@test.com,"Hello, ""world"""
        Lazamon<two@test.com>,Laȝamon 😀 klâwen
    '''))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge in tmpdir with defaults, which includes dry run
    with tmpdir.as_cwd():
        output = sh.mailmerge(
            "--no-limit",
            "--output-format", "raw",
        )

    # Decode output and remove date
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")

    # Remove the Date string, which will be different each time
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # The long output string below is the correct answer with Python 3.  With
    # Python 2, we get a few differences in newlines.  We'll just query-replace
    # those known mismatches so that the equality test passes.
    stdout = stdout.replace(
        "TGHInWFtb24g8J+YgCBrbMOid2VuCgoK",
        "TGHInWFtb24g8J+YgCBrbMOid2VuCgo=",
    )
    stdout = stdout.replace(
        "Pgo8L2h0bWw+Cgo=",
        "Pgo8L2h0bWw+Cg==",
    )
    stdout = stdout.replace('Hello, "world"\n\n\n\n', 'Hello, "world"\n\n\n')
    stdout = stdout.replace('</html>\n\n\n', '</html>\n\n')

    # Verify stdout and stderr after above corrections
    assert stderr == ""
    assert stdout == textwrap.dedent(u"""\
        >>> message 1
        TO: one@test.com
        FROM: from@test.com
        CC: cc1@test.com, cc2@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"
        Date: REDACTED

        This is a MIME-encoded message. If you are seeing this, your mail
        reader is old.

        --boundary
        MIME-Version: 1.0
        Content-Type: text/plain; charset="us-ascii"
        Content-Transfer-Encoding: 7bit

        Hello, "world"


        --boundary
        MIME-Version: 1.0
        Content-Type: text/html; charset="us-ascii"
        Content-Transfer-Encoding: 7bit

        <html>
          <body>
            <p>Hello, "world"</p>
          </body>
        </html>

        --boundary
        Content-Type: application/octet-stream; Name="attachment1.txt"
        MIME-Version: 1.0
        Content-Transfer-Encoding: base64
        Content-Disposition: attachment; filename="attachment1.txt"

        SGVsbG8gd29ybGQK

        --boundary
        Content-Type: application/octet-stream; Name="attachment2.csv"
        MIME-Version: 1.0
        Content-Transfer-Encoding: base64
        Content-Disposition: attachment; filename="attachment2.csv"

        aGVsbG8sbWFpbG1lcmdlCg==

        --boundary--
        >>> message 1 sent
        >>> message 2
        TO: Lazamon<two@test.com>
        FROM: from@test.com
        CC: cc1@test.com, cc2@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"
        Date: REDACTED

        This is a MIME-encoded message. If you are seeing this, your mail
        reader is old.

        --boundary
        MIME-Version: 1.0
        Content-Type: text/plain; charset="utf-8"
        Content-Transfer-Encoding: base64

        TGHInWFtb24g8J+YgCBrbMOid2VuCgo=

        --boundary
        MIME-Version: 1.0
        Content-Type: text/html; charset="utf-8"
        Content-Transfer-Encoding: base64

        PGh0bWw+CiAgPGJvZHk+CiAgICA8cD5MYcidYW1vbiDwn5iAIGtsw6J3ZW48L3A+CiAgPC9ib2R5
        Pgo8L2h0bWw+Cg==

        --boundary
        Content-Type: application/octet-stream; Name="attachment1.txt"
        MIME-Version: 1.0
        Content-Transfer-Encoding: base64
        Content-Disposition: attachment; filename="attachment1.txt"

        SGVsbG8gd29ybGQK

        --boundary
        Content-Type: application/octet-stream; Name="attachment2.csv"
        MIME-Version: 1.0
        Content-Transfer-Encoding: base64
        Content-Disposition: attachment; filename="attachment2.csv"

        aGVsbG8sbWFpbG1lcmdlCg==

        --boundary--
        >>> message 2 sent
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)


def test_resume(tmpdir):
    """Verify --resume option starts "in the middle" of the database."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        hello
        world
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge
    with tmpdir.as_cwd():
        output = sh.mailmerge("--resume", "2", "--no-limit")

    # Verify only second message was sent
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")
    assert stderr == ""
    assert "hello" not in stdout
    assert "message 1 sent" not in stdout
    assert "world" in stdout
    assert "message 2 sent" in stdout


def test_resume_too_small(tmpdir):
    """Verify --resume <= 0 prints an error message."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        hello
        world
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run "mailmerge --resume 0" and check output
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_2) as error:
        sh.mailmerge("--resume", "0")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "Invalid value" in stderr

    # Run "mailmerge --resume -1" and check output
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_2) as error:
        sh.mailmerge("--resume", "-1")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "Invalid value" in stderr


def test_resume_too_big(tmpdir):
    """Verify --resume > database does nothing."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        hello
        world
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run and check output
    with tmpdir.as_cwd():
        output = sh.mailmerge("--resume", "3", "--no-limit")
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")
    assert "sent message" not in stdout
    assert stderr == ""


def test_resume_hint_on_config_error(tmpdir):
    """Verify *no* --resume hint when error is after first message."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Database with error on second entry
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        hello
        "world
    """))

    # Server config missing port
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
    """))

    # Run and check output
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        sh.mailmerge()
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "--resume 1" not in stderr


def test_resume_hint_on_csv_error(tmpdir):
    """Verify --resume hint after CSV error."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Database with unmatched quote on second entry
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        hello
        "world
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run and check output
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_1) as error:
        sh.mailmerge("--resume", "2", "--no-limit")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert "--resume 2" in stderr


def test_other_mime_type(tmpdir):
    """Verify output with a MIME type that's not text or an attachment."""
    # Template containing a pdf
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
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
    """))

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        one@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge
    with tmpdir.as_cwd():
        output = sh.mailmerge()

    # Verify output
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")
    assert stderr == ""
    stdout = stdout.replace("\n\n\n\n", "\n\n\n")
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)
    assert stdout == textwrap.dedent(u"""\
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

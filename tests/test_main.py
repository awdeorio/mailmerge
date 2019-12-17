"""
System tests.

Andrew DeOrio <awdeorio@umich.edu>
"""
import re
import textwrap
import sh

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

# The sh library triggers lot of false no-member errors
# pylint: disable=no-member


def test_stdout(tmpdir):
    """Verify stdout and stderr with dry run on simple input files."""
    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>

        Hi, {{name}},

        Your number is {{number}}.
    """))

    # Simple database
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email,name,number
        myself@mydomain.com,"Myself",17
        bob@bobdomain.com,"Bob",42
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
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
    assert stdout == textwrap.dedent(u"""\
        >>> message 0
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
        """)


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


def test_bad_limit(tmpdir):
    """Verify --limit with bad value."""
    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Hello world
    """))

    # Simple database with two entries
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        one@test.com
        two@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
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
        "--limit", "-1",
        _ok_code=2,
    )
    assert "Error: Invalid value" in output.stderr.decode("utf-8")


def test_limit_combo(tmpdir):
    """Verify --limit 1 --no-limit results in no limit."""
    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Hello world
    """))

    # Simple database with two entries
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        one@test.com
        two@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
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


def test_bad_template_database(tmpdir):
    """Template mismatch with database header should produce an error."""
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
    config_path = Path(tmpdir/"server.conf")
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


def test_bad_database():
    """Database read error should produce a sane error."""
    assert False, "IMPLEMENT ME"


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
    config_path = Path(tmpdir/"server.conf")
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


def test_attachment(tmpdir):
    """Verify attachments feature output."""
    # First attachment
    attachment1_path = Path(tmpdir/"attachment1.txt")
    attachment1_path.write_text(u"Hello world\n")

    # Second attachment
    attachment2_path = Path(tmpdir/"attachment2.txt")
    attachment2_path.write_text(u"Hello mailmerge\n")

    # Template with attachment header
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com
        ATTACHMENT: attachment1.txt
        ATTACHMENT: attachment2.txt

        Hello world
    """))

    # Simple database
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        to@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
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
    )

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert "Hello world" in output  # message
    assert "SGVsbG8gd29ybGQK" in output  # attachment1
    assert "SGVsbG8gbWFpbG1lcmdlCg" in output # attachment2
    assert "attached attachment1.txt" in output
    assert "attached attachment2.txt" in output


def test_utf8_template(tmpdir):
    """Message is utf-8 encoded when only the template contains utf-8 chars."""
    # Template with UTF-8 characters and emoji
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Laȝamon 😀 klâwen
    """))

    # Simple database without utf-8 characters
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        to@test.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
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
    )

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert u"TGHInWFtb24g8J+YgCBrbMOid2Vu" in output


def test_utf8_database(tmpdir):
    """Message is utf-8 encoded when only the databse contains utf-8 chars."""
    # Simple template without UTF-8 characters
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Database with utf-8 characters and emoji
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        Laȝamon 😀 klâwen
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
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
    )

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert u"TGHInWFtb24g8J+YgCBrbMOid2Vu" in output


def test_complicated(tmpdir):
    """Complicated end-to-end test.

    Includes templating, TO, CC, BCC, UTF8 characters, emoji, attachments, and
    Markdown.
    """
    # First attachment
    attachment1_path = Path(tmpdir/"attachment1.txt")
    attachment1_path.write_text(u"Hello world\n")

    # Second attachment
    attachment2_path = Path(tmpdir/"attachment2.txt")
    attachment2_path.write_text(u"Hello mailmerge\n")

    # Third attachment
    attachment3_path = Path(tmpdir/"attachment3.tar.gz")
    attachment3_path.write_text(u"FIXME binary\n")  # FIXME binary

    # Template with attachment header
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com
        CC: cc1@test.com, cc2@test.com
        BCC: bcc1@test.com, bcc2@test.com
        ATTACHMENT: attachment1.txt
        ATTACHMENT: attachment2.txt
        ATTACHMENT: attachment3.tar.gz

        {{message}}
    """))

    # Simple database
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email,message
        one@test.com,"Hello \"world\""
        Laȝamon <lam@test.com>,Laȝamon emoji \xf0\x9f\x98\x80 klâwen
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
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
        "--dry-run",  # FIXME
    )

    # Verify output
    assert output.stderr.decode("utf-8") == ""
    assert False

# coding=utf-8
# Python 2 source containing unicode https://www.python.org/dev/peps/pep-0263/
"""
System tests focused on CLI output.

Andrew DeOrio <awdeorio@umich.edu>

pytest tmpdir docs:
http://doc.pytest.org/en/latest/tmpdir.html#the-tmpdir-fixture
"""
import re
import textwrap
import sh
import blessings
import pytest

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
        "--output-format", "text",
    )

    # Verify mailmerge output.  We'll filter out the Date header because it
    # won't match exactly.
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")
    assert stderr == ""
    assert "Date:" in stdout
    stdout = re.sub(r"Date.*\n", "", stdout)
    assert stdout == textwrap.dedent(u"""\
        >>> message 1
        TO: myself@mydomain.com
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>
        MIME-Version: 1.0
        Content-Type: text/plain; charset="us-ascii"
        Content-Transfer-Encoding: 7bit

        Hi, Myself,

        Your number is 17.

        >>> message 1 sent
        >>> message 2
        TO: bob@bobdomain.com
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>
        MIME-Version: 1.0
        Content-Type: text/plain; charset="us-ascii"
        Content-Transfer-Encoding: 7bit

        Hi, Bob,

        Your number is 42.

        >>> message 2 sent
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
        """)


def test_stdout_utf8(tmpdir):
    """Verify human-readable output when template contains utf-8."""
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        Laȝamon 😀 klâwen
    """))

    # Simple database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email
        myself@mydomain.com
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge with defaults, which includes dry-run
    with tmpdir.as_cwd():
        output = sh.mailmerge("--output-format", "text")

    # Verify mailmerge output.  We'll filter out the Date header because it
    # won't match exactly.
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")
    assert stderr == ""
    assert "Date:" in stdout
    stdout = re.sub(r"Date.*\n", "", stdout)
    assert stdout == textwrap.dedent(u"""\
        >>> message 1
        TO: to@test.com
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: text/plain; charset="utf-8"
        Content-Transfer-Encoding: base64

        Laȝamon 😀 klâwen

        >>> message 1 sent
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)  # noqa: E501


def test_english(tmpdir):
    """Verify correct English, message vs. messages."""
    # Blank message
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com
    """))

    # Database with 2 entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        dummy
        1
        2
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge with several limits
    with tmpdir.as_cwd():
        output = sh.mailmerge("--limit", "0")
        assert "Limit was 0 messages." in output
        output = sh.mailmerge("--limit", "1")
        assert "Limit was 1 message." in output
        output = sh.mailmerge("--limit", "2")
        assert "Limit was 2 messages." in output


def test_output_format_bad(tmpdir):
    """Verify bad output format."""
    with tmpdir.as_cwd(), pytest.raises(sh.ErrorReturnCode_2) as error:
        sh.mailmerge("--output-format", "bad")
    stdout = error.value.stdout.decode("utf-8")
    stderr = error.value.stderr.decode("utf-8")
    assert stdout == ""
    assert 'Invalid value for "--output-format"' in stderr
    assert "invalid choice: bad." in stderr


def test_output_format_raw(tmpdir):
    """Verify raw output format."""
    # Attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text(u"Hello world\n")

    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Laȝamon 😀 klâwen
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
        output = sh.mailmerge("--output-format", "raw")
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")

    # Remove the Date string, which will be different each time
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert stderr == ""
    assert stdout == textwrap.dedent("""\
        >>> message 1
        TO: to@test.com
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: text/plain; charset="utf-8"
        Content-Transfer-Encoding: base64
        Date: REDACTED

        TGHInWFtb24g8J+YgCBrbMOid2Vu

        >>> message 1 sent
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """)  # noqa: E501


def test_output_format_text(tmpdir):
    """Verify text output format."""
    # Attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text(u"Hello world\n")

    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com

        Laȝamon 😀 klâwen
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
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")

    # Remove the Date string, which will be different each time
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert stderr == ""
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


def test_output_format_colorized(tmpdir):
    """Verify colorized output format."""
    # Attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text(u"Hello world\n")

    # HTML template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"

        This is a MIME-encoded message. If you are seeing this, your mail
        reader is old.

        --boundary
        Content-Type: text/plain; charset=us-ascii

        Laȝamon 😀 klâwen

        --boundary
        Content-Type: text/html; charset=us-ascii

        <html>
          <body>
            <p>Laȝamon 😀 klâwen</p>
          </body>
        </html>
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
        output = sh.mailmerge("--output-format", "colorized")
    stdout = output.stdout.decode("utf-8")
    stderr = output.stderr.decode("utf-8")

    # Remove the Date string, which will be different each time
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert stderr == ""
    assert stdout == textwrap.dedent(u"""\
        {t.reverse_bold_cyan}>>> message 1{t.normal}
        TO: to@test.com
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"
        Date: REDACTED

        {t.cyan}>>> message part: text/plain{t.normal}
        Laȝamon 😀 klâwen


        {t.cyan}>>> message part: text/html{t.normal}
        <html>
          <body>
            <p>Laȝamon 😀 klâwen</p>
          </body>
        </html>

        {t.reverse_bold_cyan}>>> message 1 sent{t.normal}
        >>> Limit was 1 message.  To remove the limit, use the --no-limit option.
        >>> This was a dry run.  To send messages, use the --no-dry-run option.
    """.format(t=blessings.Terminal(force_styling=True)))  # noqa: E501

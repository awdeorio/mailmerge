"""
System tests focused on CLI output.

Andrew DeOrio <awdeorio@umich.edu>

pytest tmpdir docs:
http://doc.pytest.org/en/latest/tmpdir.html#the-tmpdir-fixture
"""
import copy
import os
import re
import textwrap
from pathlib import Path
import click.testing
from mailmerge.__main__ import main


def test_stdout(tmpdir):
    """Verify stdout and stderr with dry run on simple input files."""
    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        SUBJECT: Testing mailmerge
        FROM: My Self <myself@mydomain.com>

        Hi, {{name}},

        Your number is {{number}}.
    """), encoding="utf8")

    # Simple database
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent("""\
        email,name,number
        myself@mydomain.com,"Myself",17
        bob@bobdomain.com,"Bob",42
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge
    runner = click.testing.CliRunner(mix_stderr=False)
    result = runner.invoke(main, [
        "--template", template_path,
        "--database", database_path,
        "--config", config_path,
        "--no-limit",
        "--dry-run",
        "--output-format", "text",
    ])
    assert not result.exception
    assert result.exit_code == 0

    # Verify mailmerge output.  We'll filter out the Date header because it
    # won't match exactly.
    assert result.stderr == ""
    assert "Date:" in result.stdout
    stdout = copy.deepcopy(result.stdout)
    stdout = re.sub(r"Date.*\n", "", stdout)
    assert stdout == textwrap.dedent("""\
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
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com

        Laȝamon 😀 klâwen
    """), encoding="utf8")

    # Simple database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email
        myself@mydomain.com
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge with defaults, which includes dry-run
    runner = click.testing.CliRunner(mix_stderr=False)
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "text"])
    assert not result.exception
    assert result.exit_code == 0

    # Verify mailmerge output.  We'll filter out the Date header because it
    # won't match exactly.
    assert result.stderr == ""
    stdout = copy.deepcopy(result.stdout)
    assert "Date:" in stdout
    stdout = re.sub(r"Date.*\n", "", stdout)
    assert stdout == textwrap.dedent("""\
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


def test_stdout_utf8_redirect(tmpdir):
    """Verify utf-8 output is properly encoded when redirected.

    UTF-8 print fails when redirecting stdout under Pythnon 2
    http://blog.mathieu-leplatre.info/python-utf-8-print-fails-when-redirecting-stdout.html
    """
    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com

        Laȝamon 😀 klâwen
    """), encoding="utf8")

    # Simple database
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        email
        myself@mydomain.com
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge.  We only care that no exceptions occur.  Note that we
    # can't use the click test runner here because it doesn't accurately
    # recreate the conditions of the bug where the redirect destination lacks
    # utf-8 encoding.
    with tmpdir.as_cwd():
        exit_code = os.system("mailmerge > mailmerge.out")
    assert exit_code == 0


def test_english(tmpdir):
    """Verify correct English, message vs. messages."""
    # Blank message
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: to@test.com
        FROM: from@test.com
    """), encoding="utf8")

    # Database with 2 entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent("""\
        dummy
        1
        2
    """), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge with several limits
    runner = click.testing.CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--limit", "0"])
    assert not result.exception
    assert result.exit_code == 0
    assert "Limit was 0 messages." in result.output
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--limit", "1"])
    assert not result.exception
    assert result.exit_code == 0
    assert "Limit was 1 message." in result.output
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--limit", "2"])
    assert not result.exception
    assert result.exit_code == 0
    assert "Limit was 2 messages." in result.output


def test_output_format_bad(tmpdir):
    """Verify bad output format."""
    runner = click.testing.CliRunner(mix_stderr=False)
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "bad"])
    assert result.exit_code == 2
    assert result.stdout == ""

    # Remove single and double quotes from error message.  Different versions
    # of the click library use different formats.
    stderr = copy.deepcopy(result.stderr)
    stderr = stderr.replace('"', "")
    stderr = stderr.replace("'", "")
    assert 'Invalid value for --output-format' in stderr


def test_output_format_raw(tmpdir):
    """Verify raw output format."""
    # Attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: from@test.com

        Laȝamon 😀 klâwen
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
    runner = click.testing.CliRunner(mix_stderr=False)
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "raw"])
    assert not result.exception
    assert result.exit_code == 0

    # Remove the Date string, which will be different each time
    stdout = copy.deepcopy(result.stdout)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert result.stderr == ""
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
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
        TO: {{email}}
        FROM: from@test.com

        Laȝamon 😀 klâwen
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
    runner = click.testing.CliRunner(mix_stderr=False)
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "text"])
    assert not result.exception
    assert result.exit_code == 0

    # Remove the Date string, which will be different each time
    stdout = copy.deepcopy(result.stdout)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output
    assert result.stderr == ""
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


def test_output_format_colorized(tmpdir):
    """Verify colorized output format."""
    # Attachment
    attachment_path = Path(tmpdir/"attachment.txt")
    attachment_path.write_text("Hello world\n", encoding="utf8")

    # HTML template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
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
    runner = click.testing.CliRunner(mix_stderr=False)
    with tmpdir.as_cwd():
        result = runner.invoke(main, ["--output-format", "colorized"])
    assert not result.exception
    assert result.exit_code == 0

    # Remove the Date string, which will be different each time
    stdout = copy.deepcopy(result.stdout)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)

    # Verify output.  The funny looking character sequences are colors.
    assert result.stderr == ""
    assert stdout == textwrap.dedent("""\
        \x1b[7m\x1b[1m\x1b[36m>>> message 1\x1b(B\x1b[m
        TO: to@test.com
        FROM: from@test.com
        MIME-Version: 1.0
        Content-Type: multipart/alternative; boundary="boundary"
        Date: REDACTED

        \x1b[36m>>> message part: text/plain\x1b(B\x1b[m
        La\u021damon \U0001f600 kl\xe2wen


        \x1b[36m>>> message part: text/html\x1b(B\x1b[m
        <html>
          <body>
            <p>La\u021damon \U0001f600 kl\xe2wen</p>
          </body>
        </html>

        \x1b[7m\x1b[1m\x1b[36m>>> message 1 sent\x1b(B\x1b[m
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
    attachment1_path.write_text("Hello world\n", encoding="utf8")

    # Second attachment
    attachment2_path = Path(tmpdir/"attachment2.csv")
    attachment2_path.write_text("hello,mailmerge\n", encoding="utf8")

    # Template with attachment header
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent("""\
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


    """), encoding="utf8")

    # Database with utf-8, emoji, quotes, and commas.  Note that quotes are
    # escaped with double quotes, not backslash.
    # https://docs.python.org/3.7/library/csv.html#csv.Dialect.doublequote
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent('''\
        email,message
        one@test.com,"Hello, ""world"""
        Lazamon<two@test.com>,Laȝamon 😀 klâwen
    '''), encoding="utf8")

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent("""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """), encoding="utf8")

    # Run mailmerge in tmpdir with defaults, which includes dry run
    runner = click.testing.CliRunner(mix_stderr=False)
    with tmpdir.as_cwd():
        result = runner.invoke(main, [
            "--no-limit",
            "--output-format", "raw",
        ])
    assert not result.exception
    assert result.exit_code == 0

    # Remove the Date and Content-ID strings, which will be different each time
    stdout = copy.deepcopy(result.stdout)
    stdout = re.sub(r"Date:.+", "Date: REDACTED", stdout, re.MULTILINE)
    stdout = re.sub(r'Content-Id:.*', '', stdout)

    # Verify stdout and stderr after above corrections
    assert result.stderr == ""
    assert stdout == textwrap.dedent("""\
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

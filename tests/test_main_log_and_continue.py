# coding=utf-8
# Python 2 source containing unicode https://www.python.org/dev/peps/pep-0263/
"""
System tests.

Andrew DeOrio <awdeorio@umich.edu>

pytest tmpdir docs:
http://doc.pytest.org/en/latest/tmpdir.html#the-tmpdir-fixture
"""
import textwrap
import sh

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

# The sh library triggers lot of false no-member errors
# pylint: disable=no-member


def test_log(tmpdir):
    """Verify --continue-on-error continues if theere is an error."""

    # Second attachment
    attachment2_path = Path(tmpdir/"attachment2.txt")
    attachment2_path.write_text(u"Hello mailmerge\n")

    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com
        ATTACHMENT: {{attachment}}

        Hello world
    """))

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email,attachment
        one@test.com,attachment1.txt
        two@test.com,attachment2.txt
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"mailmerge_server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = open-smtp.example.com
        port = 25
    """))

    # Run mailmerge
    log = tmpdir.join('log.csv')
    with tmpdir.as_cwd():
        output = sh.mailmerge(
            "--no-limit", "--continue-on-error",
            "--log", "log.csv"
        )
    stderr = output.stderr.decode("utf-8")
    assert "message 1 sent" not in output
    assert "message 2 sent" in output
    assert "Error on message 1" in stderr
    assert "Attachment not found" in stderr
    assert log.read() == textwrap.dedent(u"""\
        number,email,log
        1,,"Attachment not found: {}/attachment1.txt"
        2,two@test.com,"OK, not sent"
    """.format(tmpdir))


def test_continue_on_error(tmpdir):
    """Verify --continue-on-error continues if theere is an error."""

    # Second attachment
    attachment2_path = Path(tmpdir/"attachment2.txt")
    attachment2_path.write_text(u"Hello mailmerge\n")

    # Simple template
    template_path = Path(tmpdir/"mailmerge_template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: {{email}}
        FROM: from@test.com
        ATTACHMENT: {{attachment}}

        Hello world
    """))

    # Simple database with two entries
    database_path = Path(tmpdir/"mailmerge_database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email,attachment
        one@test.com,attachment1.txt
        two@test.com,attachment2.txt
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
        output = sh.mailmerge("--no-limit", "--continue-on-error")
    stderr = output.stderr.decode("utf-8")
    assert "message 1 sent" not in output
    assert "message 2 sent" in output
    assert "Error on message 1" in stderr
    assert "Attachment not found" in stderr

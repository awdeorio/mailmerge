"""
End-to-end tests with a live SMTP server.

Andrew DeOrio <awdeorio@umich.edu>
"""
import textwrap
import ssl
from pathlib import Path
import pkg_resources  # FIXME third party dep?
import sh
import pytest
import aiosmtpd.controller
import aiosmtpd.handlers


# The sh library triggers lot of false no-member errors
# pylint: disable=no-member

# Test fixtures need to be inputs, but aren't always used
# pylint: disable=unused-argument


@pytest.fixture(name='live_smtp_server')
def setup_teardown_live_smtp_server():
    """Start a message-swallowing SMTP server in a separate thread."""
    controller = aiosmtpd.controller.Controller(
        aiosmtpd.handlers.Sink(),
        port=8025,
    )
    controller.start()
    yield controller
    controller.stop()


def test_no_security(tmpdir, live_smtp_server):
    """Connect to a live server with no authentication."""
    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Simple database
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        hello
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = localhost
        port = 8025
    """))

    # Run mailmerge
    sh.mailmerge(
        "--template", template_path,
        "--database", database_path,
        "--config", config_path,
        "--no-dry-run",
    )


@pytest.fixture(name='live_smtp_server_ssl_tls')
def setup_teardown_live_smtp_server_ssl_tls():
    """Start a message-swallowing SMTP server in a separate thread."""
    tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    tls_context.load_cert_chain(
        pkg_resources.resource_filename('aiosmtpd.tests.certs', 'server.crt'),
        pkg_resources.resource_filename('aiosmtpd.tests.certs', 'server.key'),
    )
    controller = aiosmtpd.controller.Controller(
        aiosmtpd.handlers.Sink(),
        port=8025,
        ssl_context=tls_context,
    )
    controller.start()
    yield controller
    controller.stop()


def test_ssl_tls(tmpdir, live_smtp_server):
    """Connect to a live server SSL/TLS security."""
    # Simple template
    template_path = Path(tmpdir/"template.txt")
    template_path.write_text(textwrap.dedent(u"""\
        TO: to@test.com
        FROM: from@test.com

        {{message}}
    """))

    # Simple database
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        message
        hello
    """))

    # Simple unsecure server config
    config_path = Path(tmpdir/"server.conf")
    config_path.write_text(textwrap.dedent(u"""\
        [smtp_server]
        host = localhost
        port = 8025
        security = SSL/TLS
        username = root
    """))

    # Run mailmerge
    sh.mailmerge(
        "--template", template_path,
        "--database", database_path,
        "--config", config_path,
        "--no-dry-run",
        _in="password",
        _tty_in=True,  # Needed to trick getpass()
    )

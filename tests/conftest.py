import logging
import pytest
import aiosmtpd.controller

logging.getLogger("sh").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)


@pytest.fixture(name='live_smtp_server')
def setup_teardown_live_smtp_server():
    """Start SMTP server in a separate thread."""
    controller = aiosmtpd.controller.Controller(
        ExampleHandler(),
        port=8025,
    )
    controller.start()

    # Transfer control to testcase
    yield controller

    # Stop server
    controller.stop()


#https://aiosmtpd.readthedocs.io/en/latest/aiosmtpd/docs/controller.html
class ExampleHandler:
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_DATA(self, server, session, envelope):
        logging.debug("Message from %s" % envelope.mail_from)
        logging.debug("Message for %s" % envelope.rcpt_tos)
        logging.debug("Message data:\n")
        logging.debug(envelope.content.decode("utf8", errors="replace"))
        logging.debug("End of message")
        return "250 Message accepted for delivery"

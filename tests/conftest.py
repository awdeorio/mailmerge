import pytest
import aiosmtpd.controller


@pytest.fixture(name='live_smtp_server')
def setup_teardown_live_smtp_server():
    """Start SMTP server in a separate thread."""
    controller = aiosmtpd.controller.Controller(ExampleHandler())
    controller.start()

    # Transfer control to testcase
    yield controller

    # Stop server
    controller.stop()


#https://aiosmtpd.readthedocs.io/en/latest/aiosmtpd/docs/controller.html
class ExampleHandler:
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        if not address.endswith('@example.com'):
            return '550 not relaying to that domain'
        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        print('Message from %s' % envelope.mail_from)
        print('Message for %s' % envelope.rcpt_tos)
        print('Message data:\n')
        print(envelope.content.decode('utf8', errors='replace'))
        print('End of message')
        return '250 Message accepted for delivery'

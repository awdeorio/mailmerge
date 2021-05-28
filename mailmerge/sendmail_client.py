"""
SMTP client reads configuration and sends message.

Andrew DeOrio <awdeorio@umich.edu>
"""
import collections
import socket
import smtplib
import configparser
import getpass
import datetime
from . import exceptions
from . import utils


# Type to store info read from config file
MailmergeConfig = collections.namedtuple(
    "MailmergeConfig",
    ["username", "host", "port", "security", "ratelimit"],
)


class SendmailClient(object):
    """Represent a client connection to an SMTP server."""

    # This class is pretty simple.  We don't need more than one public method.
    # pylint: disable=too-few-public-methods
    #
    # We need to inherit from object for Python 2 compantibility
    # https://python-future.org/compatible_idioms.html#custom-class-behaviour
    # pylint: disable=bad-option-value,useless-object-inheritance

    def __init__(self, config_path, dry_run=False):
        """Read configuration from server configuration file."""
        self.dry_run = dry_run
        self.password = None
        self.ratelimit = None
        self.lastsent = None
        try:
            parser = configparser.RawConfigParser()
            parser.read(str(config_path))
            host = parser.get("smtp_server", "host")
            port = parser.getint("smtp_server", "port")
            security = parser.get("smtp_server", "security", fallback=None)
            username = parser.get("smtp_server", "username", fallback=None)
            ratelimit = parser.getint("smtp_server", "ratelimit", fallback=0)
        except (configparser.Error, ValueError) as err:
            raise exceptions.MailmergeError(
                "{}: {}".format(config_path, err)
            )

        # Coerce legacy option "security = Never"
        if security == "Never":
            security = None

        # Verify security type
        if security not in [None, "SSL/TLS", "STARTTLS"]:
            raise exceptions.MailmergeError(
                "{}: unrecognized security type: '{}'"
                .format(config_path, security)
            )

        # Save validated configuration
        self.config = MailmergeConfig(username, host, port, security, ratelimit)

    def sendmail(self, sender, recipients, message):
        """Send email message.

        Note that we can't use the elegant smtp.send_message(message)" because
        Python 2 doesn't support it.  Both Python 2 and Python 3 support
        smtp.sendmail(sender, recipients, flattened_message_str).
        """
        # no-member errors are endemic to the socket library
        # pylint: disable=no-member

        if self.dry_run:
            return

        # Check if we've hit the rate limit
        waittime = datetime.timedelta(minutes=1 / self.config.ratelimit)
        now = datetime.datetime.now()
        if self.config.ratelimit and self.lastsent:
            if now - self.lastsent < waittime:
                raise exceptions.MailmergeRateLimitError()

        # Ask for password if necessary
        if self.config.security is not None and self.password is None:
            prompt = ">>> password for {} on {}: ".format(
                self.config.username, self.config.host)
            self.password = getpass.getpass(prompt)

        # Send
        try:
            message_flattened = utils.flatten_message(message)
            host, port = self.config.host, self.config.port
            if self.config.security == "SSL/TLS":
                with smtplib.SMTP_SSL(host, port) as smtp:
                    smtp.login(self.config.username, self.password)
                    smtp.sendmail(sender, recipients, message_flattened)
            elif self.config.security == "STARTTLS":
                with smtplib.SMTP(host, port) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(self.config.username, self.password)
                    smtp.sendmail(sender, recipients, message_flattened)
            elif self.config.security is None:
                with smtplib.SMTP(host, port) as smtp:
                    smtp.sendmail(sender, recipients, message_flattened)
        except smtplib.SMTPAuthenticationError as err:
            raise exceptions.MailmergeError(
                "{}:{} failed to authenticate user '{}': {}"
                .format(host, port, self.config.username, err)
            )
        except smtplib.SMTPException as err:
            raise exceptions.MailmergeError(
                "{}:{} failed to send message: {}"
                .format(host, port, err)
            )
        except socket.error as err:
            raise exceptions.MailmergeError(
                "{}:{} failed to connect to server: {}"
                .format(host, port, err)
            )

        # Update timestamp of last sent message
        self.lastsent = now

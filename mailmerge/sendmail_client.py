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


# Type to store info read from config file
MailmergeConfig = collections.namedtuple(
    "MailmergeConfig",
    ["username", "host", "port", "security", "ratelimit"],
)


class SendmailClient:
    """Represent a client connection to an SMTP server."""

    def __init__(self, config_path, dry_run=False):
        """Read configuration from server configuration file."""
        self.config_path = config_path
        self.dry_run = dry_run  # Do not send real messages
        self.config = None      # Config read from config_path by read_config()
        self.password = None    # Password read from stdin
        self.lastsent = None    # Timestamp of last successful send
        self.read_config()

    def read_config(self):
        """Read configuration file and return a MailmergeConfig object."""
        try:
            parser = configparser.RawConfigParser()
            parser.read(str(self.config_path))
            host = parser.get("smtp_server", "host")
            port = parser.getint("smtp_server", "port")
            security = parser.get("smtp_server", "security", fallback=None)
            username = parser.get("smtp_server", "username", fallback=None)
            ratelimit = parser.getint("smtp_server", "ratelimit", fallback=0)
        except (configparser.Error, ValueError) as err:
            raise exceptions.MailmergeError(f"{self.config_path}: {err}")

        # Coerce legacy option "security = Never"
        if security == "Never":
            security = None

        # Verify security type
        if security not in [None, "SSL/TLS", "STARTTLS", "PLAIN"]:
            raise exceptions.MailmergeError(
                f"{self.config_path}: unrecognized security type: '{security}'"
            )

        # Verify username
        if security is not None and username is None:
            raise exceptions.MailmergeError(
                f"{self.config_path}: username is required for "
                f"security type '{security}'"
            )

        # Save validated configuration
        self.config = MailmergeConfig(
            username, host, port, security, ratelimit,
        )

    def sendmail(self, sender, recipients, message):
        """Send email message."""
        if self.dry_run:
            return

        # Check if we've hit the rate limit
        now = datetime.datetime.now()
        if self.config.ratelimit and self.lastsent:
            waittime = datetime.timedelta(minutes=1.0 / self.config.ratelimit)
            if now - self.lastsent < waittime:
                raise exceptions.MailmergeRateLimitError()

        # Ask for password if necessary
        if self.config.security is not None and self.password is None:
            self.password = getpass.getpass(
                f">>> password for {self.config.username} on "
                f"{self.config.host}: "
            )

        # Send
        try:
            message_flattened = str(message)
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
            elif self.config.security == "PLAIN":
                with smtplib.SMTP(host, port) as smtp:
                    smtp.login(self.config.username, self.password)
                    smtp.sendmail(sender, recipients, message_flattened)
            elif self.config.security is None:
                with smtplib.SMTP(host, port) as smtp:
                    smtp.sendmail(sender, recipients, message_flattened)
        except smtplib.SMTPAuthenticationError as err:
            raise exceptions.MailmergeError(
                f"{host}:{port} failed to authenticate "
                f"user '{self.config.username}': {err}"
            )
        except smtplib.SMTPException as err:
            raise exceptions.MailmergeError(
                f"{host}:{port} failed to send message: {err}"
            )
        except socket.error as err:
            raise exceptions.MailmergeError(
                f"{host}:{port} failed to connect to server: {err}"
            )

        # Update timestamp of last sent message
        self.lastsent = now

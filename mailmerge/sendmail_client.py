"""
SMTP client reads configuration and sends message.

Andrew DeOrio <awdeorio@umich.edu>
"""
import socket
import smtplib
import configparser
import getpass
import datetime
from . import exceptions
from . import utils


class SendmailClient(object):
    """Represent a client connection to an SMTP server."""

    # This class is pretty simple.  We don't need more than one public method.
    # pylint: disable=too-few-public-methods

    # For the internal state and rate limiting we need more then 7 attributes
    # pylint: disable=too-many-instance-attributes

    #
    # We need to inherit from object for Python 2 compantibility
    # https://python-future.org/compatible_idioms.html#custom-class-behaviour
    # pylint: disable=bad-option-value,useless-object-inheritance

    def __init__(self, config_path, dry_run=False):
        """Read configuration from server configuration file."""
        self.config_path = config_path
        self.dry_run = dry_run
        self.username = None
        self.password = None
        now = datetime.datetime.now()
        self.rate_time = now.hour*100+now.minute
        self.rate_count = 0
        try:
            config = configparser.RawConfigParser()
            config.read(str(config_path))
            self.host = config.get("smtp_server", "host")
            self.port = config.getint("smtp_server", "port")
            self.security = config.get("smtp_server", "security",
                                       fallback=None)
            if self.security == "Never":
                # Coerce legacy option "security = Never"
                self.security = None
            if self.security is not None:
                # Read username only if needed
                self.username = config.get("smtp_server", "username")
            self.rate = int(config.get("smtp_server", "rate", fallback=0))
            if self.rate:
                self.rate_budget = self.rate
        except configparser.Error as err:
            raise exceptions.MailmergeError(
                "{}: {}".format(self.config_path, err)
            )

        # Verify security type
        if self.security not in [None, "SSL/TLS", "STARTTLS"]:
            raise exceptions.MailmergeError(
                "{}: unrecognized security type: '{}'"
                .format(self.config_path, self.security)
            )

    def sendmail(self, sender, recipients, message):
        """Send email message.

        Note that we can't use the elegant smtp.send_message(message)" because
        Python 2 doesn't support it.  Both Python 2 and Python 3 support
        smtp.sendmail(sender, recipients, flattened_message_str).
        """
        if self.rate:
            now = datetime.datetime.now()
            now_time = now.hour*100+now.minute
            # Is it a new minute?
            if now_time != self.rate_time:
                self.rate_budget = self.rate
                self.rate_time = now_time

            self.rate_budget = self.rate_budget - 1
            if self.rate_budget < 0:
                # We don't have any budget anymore this minute, return
                # the number of seconds to wait
                return 60 - now.second

        if self.dry_run:
            return 0

        # Ask for password if necessary
        if self.security is not None and self.password is None:
            prompt = ">>> password for {} on {}: ".format(
                self.username, self.host)
            self.password = getpass.getpass(prompt)

        # Send
        try:
            message_flattened = utils.flatten_message(message)
            if self.security == "SSL/TLS":
                with smtplib.SMTP_SSL(self.host, self.port) as smtp:
                    smtp.login(self.username, self.password)
                    smtp.sendmail(sender, recipients, message_flattened)
            elif self.security == "STARTTLS":
                with smtplib.SMTP(self.host, self.port) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(self.username, self.password)
                    smtp.sendmail(sender, recipients, message_flattened)
            elif self.security is None:
                with smtplib.SMTP(self.host, self.port) as smtp:
                    smtp.sendmail(sender, recipients, message_flattened)
        except smtplib.SMTPAuthenticationError as err:
            raise exceptions.MailmergeError(
                "{}:{} failed to authenticate user '{}': {}"
                .format(self.host, self.port, self.username, err)
            )
        except smtplib.SMTPException as err:
            raise exceptions.MailmergeError(
                "{}:{} failed to send message: {}"
                .format(self.host, self.port, err)
            )
        except socket.error as err:
            raise exceptions.MailmergeError(
                "{}:{} failed to connect to server: {}"
                .format(self.host, self.port, err)
            )
        # All ok, return nothing
        return 0

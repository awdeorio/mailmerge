"""
SMTP client reads configuration and sends message.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
import smtplib
import configparser
import getpass


class SendmailClient(object):
    """Represent a client connection to an SMTP server."""

    # This class is pretty simple.  We don't need more than one public method.
    # pylint: disable=too-few-public-methods
    #
    # We need to inherit from object for Python 2 compantibility
    # https://python-future.org/compatible_idioms.html#custom-class-behaviour
    # pylint: disable=bad-option-value,useless-object-inheritance

    def __init__(self, config_filename, dry_run=False):
        """Read configuration from config_filename."""
        config = configparser.RawConfigParser()
        config.read(config_filename)
        self.dry_run = dry_run
        self.host = config.get("smtp_server", "host")
        self.port = config.getint("smtp_server", "port")
        self.security = config.get("smtp_server", "security")
        self.username = config.get("smtp_server", "username", fallback=None)
        self.password = os.environ.get('EMAIL_PASSWORD')

    def sendmail(self, sender, recipients, message):
        """Send email message."""
        if self.dry_run:
            return

        # Connect
        if self.security == "SSL/TLS":
            smtp = smtplib.SMTP_SSL(self.host, self.port)
        elif self.security == "STARTTLS":
            smtp = smtplib.SMTP(self.host, self.port)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
        elif self.security == "Never":
            smtp = smtplib.SMTP(self.host, self.port)
        else:
            raise configparser.Error("Unrecognized security type: {}".format(
                self.security))

        # Ask for password if necessary
        if self.security != "Never" and self.password is None:
            prompt = ">>> password for {} on {}: ".format(
                self.username, self.host)
            self.password = getpass.getpass(prompt)

        # Authenticate
        if self.security != "Never":
            assert self.username
            assert self.password
            smtp.login(self.username, self.password)

        # Send message.  Note that we can't use the elegant
        # "smtp.send_message(message)" because that's python3 only
        smtp.sendmail(sender, recipients, message.as_string())
        smtp.close()

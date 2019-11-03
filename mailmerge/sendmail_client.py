"""SMTP client reads configuration and sends message."""
import smtplib
import configparser
import getpass


class SendmailClient:
    """Represent a client connection to an SMTP server."""

    def __init__(self, config_filename, dry_run=False):
        """Read configuration from config_filename."""
        config = configparser.RawConfigParser()
        config.read(config_filename)
        self.dry_run = dry_run
        self.host = config.get("smtp_server", "host")
        self.port = config.getint("smtp_server", "port")
        self.security = config.get("smtp_server", "security")

        if self.security != "Never":
            self.username = config.get("smtp_server", "username")
            prompt = ">>> password for {} on {}: ".format(
                self.username, self.host)
            self.password = getpass.getpass(prompt)

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

        # Authenticate
        if self.security != "Never":
            assert self.username
            assert self.password
            smtp.login(self.username, self.password)

        # Send message.  Note that we can't use the elegant
        # "smtp.send_message(message)" because that's python3 only
        smtp.sendmail(sender, recipients, message.as_string())
        smtp.close()

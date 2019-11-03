"""
Mail merge using CSV database and jinja2 template email.

API implementation.

Andrew DeOrio <awdeorio@umich.edu>
"""
from __future__ import print_function
import io
import smtplib
import configparser
import getpass
from .message_template import MessageTemplate

# NOTE: Python 2.x UTF8 support requires csv and email backports
try:
    from backports import csv
except ImportError:
    import csv


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


def read_csv_database(database_path):
    """Read database CSV file, providing one line at a time."""
    with io.open(database_path, "r") as database_file:
        reader = csv.DictReader(database_file)
        for row in reader:
            yield row


def enumerate_limit(iterable, limit):
    """Enumerate iterable, stopping after limit iterations.

    When limit == -1, enumerate entire iterable.
    """
    for i, value in enumerate(iterable):
        if limit >= 0 and i >= limit:
            return
        yield i, value


def sendall(database_path, template_path, config_path, limit, dry_run):
    """Render a template message and send on each iteration."""
    message_template = MessageTemplate(template_path)
    csv_database = read_csv_database(database_path)
    sendmail_client = SendmailClient(config_path, dry_run)
    for i, row in enumerate_limit(csv_database, limit):
        sender, recipients, message = message_template.render(row)
        sendmail_client.sendmail(sender, recipients, message)
        yield sender, recipients, message, i

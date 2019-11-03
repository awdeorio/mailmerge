"""Utility functions."""
import io
from .message_template import MessageTemplate
from .sendmail_client import SendmailClient

# Python 2.x UTF8 support requires csv backport
try:
    from backports import csv
except ImportError:
    import csv


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

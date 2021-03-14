"""
SMTP client reads configuration and sends message.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os.path

from .exceptions import MailmergeError


class MailmergeLog():
    """Represents a log file."""

    def __init__(self, path, dry_run=False):
        """Open a log file for output."""
        self.path = path
        self.dry_run = dry_run
        try:
            if self.path:
                if os.path.isfile(self.path):
                    self.file = open(self.path, "a+")
                else:
                    self.file = open(self.path, "w+")
                    print("number,email,log", file=self.file)
            else:
                self.file = None
        except MailmergeError as err:
            raise MailmergeError(
                "{}: {}".format(
                    self.path, "Unable to open log file"
                )
            ) from err

    def log(self, number, recipients, message):
        """Write a message to a log file."""
        if self.file:
            if len(recipients) == 0:
                recipients = [""]
            try:
                for email in recipients:
                    print(
                        "{},{},\"{}\"".format(
                            number, email, message
                        ),
                        file=self.file
                    )
            except MailmergeError as err:
                raise MailmergeError(
                    "{}: {}".format(
                        self.path, "Unable to write to logfile"
                    )
                ) from err

    def close(self):
        """Close a log file."""
        if self.file:
            try:
                self.file.close()
                self.file = None
            except MailmergeError as err:
                raise MailmergeError(
                    "{}: {}".format(
                        self.path, "Unable to close logfile"
                    )
                ) from err

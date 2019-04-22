"""Base test class for SMTP tests."""
import os
import unittest
from mailmerge.smtp_dummy import SMTP_dummy


class TestSMTPBase(unittest.TestCase):
    """Base test class for SMTP tests."""

    DATABASE_FILENAME = "test_smtp_base.database.csv"
    SERVER_CONFIG_FILENAME = "server_dummy.conf"

    def setUp(self):
        """Change directory to tests/ before any unit test."""
        os.chdir(os.path.dirname(__file__))

        # Initialize dummy SMTP server
        self.smtp = SMTP_dummy()
        self.smtp.clear()

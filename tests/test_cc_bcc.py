"""Test messages with CC and BCC fields."""
import os
import unittest
import mailmerge
from mailmerge.smtp_dummy import SMTP_dummy


class TestCCBCC(unittest.TestCase):
    """Test messages with CC and BCC fields."""
    def setUp(self):
        """Change directory to tests/ before any unit test."""
        os.chdir(os.path.dirname(__file__))

        # Initialize dummy SMTP server
        self.smtp = SMTP_dummy()
        self.smtp.clear()

    def test_cc_bcc(self):
        """CC recipients should receive a copy."""
        mailmerge.api.main(
            database_filename="test_cc_bcc.database.csv",
            template_filename="test_cc_bcc.template.txt",
            config_filename="server_dummy.conf",
            dry_run=False,
            no_limit=False,
        )

        # Check SMTP server after
        self.assertEqual(self.smtp.msg_from, "My Self <myself@mydomain.com>")
        recipients = ["myself@mydomain.com",
                      "mycolleague@mydomain.com",
                      "secret@mydomain.com"]
        self.assertEqual(self.smtp.msg_to, recipients)

        # Make sure BCC recipients are *not* in the message
        self.assertNotIn("BCC", self.smtp.msg)
        self.assertNotIn("secret@mydomain.com", self.smtp.msg)
        self.assertNotIn("Secret", self.smtp.msg)

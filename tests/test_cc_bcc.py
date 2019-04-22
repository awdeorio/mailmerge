"""Test messages with CC and BCC fields."""
import mailmerge
from tests.test_smtp_base import TestSMTPBase


class TestCCBCC(TestSMTPBase):
    """Test messages with CC and BCC fields."""

    def test_cc_bcc(self):
        """CC recipients should receive a copy."""
        mailmerge.api.main(
            database_filename=self.DATABASE_FILENAME,
            config_filename=self.SERVER_CONFIG_FILENAME,
            template_filename="test_cc_bcc.template.txt",
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

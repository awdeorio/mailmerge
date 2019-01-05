"""Test messages with attachments."""
import os
import unittest
import mailmerge
from mailmerge.smtp_dummy import SMTP_dummy
import future.backports.email as email


class TestSendAttachment(unittest.TestCase):
    """Test messages with attachments."""
    def setUp(self):
        """Change directory to tests/ before any unit test."""
        os.chdir(os.path.dirname(__file__))

        # Initialize dummy SMTP server
        self.smtp = SMTP_dummy()
        self.smtp.clear()

    def _validateMessageContents(self, message):
        """Validate the contents and attachments of the message."""
        self.assertTrue(message.is_multipart())
        # Make sure the attachments are all present and valid
        email_body_present = False
        expected_attachments = {
            "test_send_attachment_1.txt": False,
            "test_send_attachment_2.pdf": False,
            "test_send_attachment_17.txt": False,
        }
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part['content-type'].startswith('text/plain'):
                # This is the email body
                email_body = part.get_payload()
                self.assertEqual(email_body, 'Hi, Myself,\n\nYour number is 17.\n')
                email_body_present = True
            elif part['content-type'].startswith('application/octet-stream'):
                # This is an attachment
                filename = part.get_param('name')
                file_contents = part.get_payload(decode=True)
                self.assertIn(filename, expected_attachments)
                self.assertFalse(expected_attachments[filename])
                with open(filename, 'rb') as f:
                    correct_file_contents = f.read()
                self.assertEqual(file_contents, correct_file_contents)
                expected_attachments[filename] = True
        self.assertTrue(email_body_present)
        self.assertNotIn(False, expected_attachments.values())

    def test_send_attachment(self):
        """Attachments should be sent as part of the email."""
        mailmerge.api.main(
            attachments_list_filename="test_send_attachment_list.txt",
            database_filename="test_send_attachment.database.csv",
            template_filename="test_send_attachment.template.txt",
            config_filename="server_dummy.conf",
            dry_run=False,
            no_limit=False,
        )

        # Check SMTP server after
        self.assertEqual(self.smtp.msg_from, "My Self <myself@mydomain.com>")
        recipients = ["myself@mydomain.com"]
        self.assertEqual(self.smtp.msg_to, recipients)

        # Check that the message is multipart
        message = email.parser.Parser().parsestr(self.smtp.msg)
        self._validateMessageContents(message)
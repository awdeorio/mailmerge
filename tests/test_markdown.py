"""Test messages with markdown."""
import future.backports.email as email
import markdown
import mailmerge
from tests.test_smtp_base import TestSMTPBase


class TestMarkdown(TestSMTPBase):
    """Test messages with markdown."""

    def _validate_message_contents(self, message):
        """Validate the contents and attachments of the message."""
        self.assertTrue(message.is_multipart())

        # Make sure there is a plaintext part and an HTML part
        payload = message.get_payload()
        self.assertEqual(len(payload), 2)

        # Ensure that the first part is plaintext and the last part
        # is HTML (as per RFC 2046)
        plaintext_contenttype = payload[0]['Content-Type']
        self.assertTrue(plaintext_contenttype.startswith("text/plain"))
        plaintext = payload[0].get_payload()

        html_contenttype = payload[1]['Content-Type']
        self.assertTrue(html_contenttype.startswith("text/html"))
        htmltext = payload[1].get_payload()

        converted_html = markdown.markdown(plaintext)
        self.assertEqual("<html><body>{}</body></html>".format(converted_html),
                         htmltext.strip())

    def test_markdown(self):
        """Markdown messages should be converted to HTML before being sent."""
        mailmerge.api.main(
            database_filename=self.DATABASE_FILENAME,
            config_filename=self.SERVER_CONFIG_FILENAME,
            template_filename="test_markdown.template.txt",
            no_limit=False,
            dry_run=False,
        )

        # Check SMTP server after
        self.assertEqual(self.smtp.msg_from, "Bob <bob@bobdomain.com>")
        recipients = ["myself@mydomain.com"]
        self.assertEqual(self.smtp.msg_to, recipients)

        # Check that the message is multipart and contains HTML text.
        message = email.parser.Parser().parsestr(self.smtp.msg)
        self._validate_message_contents(message)

"""
Mail merge module importable API.

Andrew DeOrio <awdeorio@umich.edu>
"""


from sendmail_client import SendmailClient
from template_message import TemplateMessage


class MailmergeError(Exception):
    """Top-level exception raised by mailmerge functions."""

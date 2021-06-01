"""Errors raised by mailmerge."""


class MailmergeError(Exception):
    """Top level exception raised by mailmerge functions."""


class MailmergeRateLimitError(MailmergeError):
    """Reuse to send message because rate limit exceeded."""

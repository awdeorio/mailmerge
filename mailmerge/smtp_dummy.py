"""Dummy SMTP API."""


class SMTP_dummy(object):  # pylint: disable=useless-object-inheritance
    # pylint: disable=invalid-name, no-self-use
    """Dummy SMTP API."""

    # Class variables track member function calls for later checking.
    msg_from = None
    msg_to = None
    msg = None

    def login(self, login, password):
        """Do nothing."""

    def sendmail(self, msg_from, msg_to, msg):
        """Remember the recipients."""
        SMTP_dummy.msg_from = msg_from
        SMTP_dummy.msg_to = msg_to
        SMTP_dummy.msg = msg

    def close(self):
        """Do nothing."""
        pass

    def clear(self):
        """Reset class variables."""
        SMTP_dummy.msg_from = None
        SMTP_dummy.msg_to = []
        SMTP_dummy.msg = None

"""Dummy SMTP API."""


class SMTP_dummy(object):
    # pylint: disable=invalid-name, no-self-use
    """Dummy SMTP API."""

    def login(self, login, password):
        """Do nothing."""
        pass

    def send_message(self, message):
        """Do nothing."""
        pass

    def sendmail(self, msg_from, msg_to, msg):
        """Do nothing."""
        pass

    def close(self):
        """Do nothing."""
        pass

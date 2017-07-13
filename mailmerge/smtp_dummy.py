class SMTP_dummy(object):
    def login(self, login, password):
        pass

    def send_message(self, message):
        pass

    def sendmail(self, msg_from, msg_to, msg):
        pass

    def close(self):
        pass

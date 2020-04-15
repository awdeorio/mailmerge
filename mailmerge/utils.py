# FIXME import style
from cStringIO import StringIO
from email.generator import Generator


def flatten_message(message):
    # https://docs.python.org/2/library/email.message.html
    fp = StringIO()
    g = Generator(fp, mangle_from_=False, maxheaderlen=78)
    g.flatten(message)
    text = fp.getvalue()
    return text

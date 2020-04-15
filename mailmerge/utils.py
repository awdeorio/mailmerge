"""
Utility functions used by multiple mailmerge modules.

Andrew DeOrio <awdeorio@umich.edu>
"""
import io
import base64
import future.backports.email as email
import future.backports.email.base64mime
import future.backports.email.generator  # pylint: disable=unused-import
import future.builtins


# Monkey patch future.backports.email library
# FIXME better comments
def header_encode_patched(header_bytes, charset='iso-8859-1'):
    """Encode a single header line with Base64 encoding in a given charset.

    charset names the character set to use to encode the header.  It defaults
    to iso-8859-1.  Base64 encoding is defined in RFC 2045.
    """
    if not header_bytes:
        return ""
    if isinstance(header_bytes, str):
        # FIXME comment
        # header_bytes = header_bytes.encode(charset)
        header_bytes = future.builtins.bytes(header_bytes, charset)
    encoded = base64.b64encode(header_bytes).decode("ascii")
    return '=?%s?b?%s?=' % (charset, encoded)

future.backports.email.base64mime.header_encode = header_encode_patched


def flatten_message(message):
    """Return message as string.

    We can't use Python 3's message.__str__() because it doesn't work on Python
    2.  We can't use message.as_string() because it errors on UTF-8 headers.

    Based on Python 2 documentation
    https://docs.python.org/2/library/email.message.html

    """
    stream = io.StringIO()
    generator = email.generator.Generator(
        stream,
        mangle_from_=False,
        maxheaderlen=78,
        policy=message.policy.clone(cte_type=u"7bit"),
    )
    generator.flatten(message)
    text = stream.getvalue()
    return text

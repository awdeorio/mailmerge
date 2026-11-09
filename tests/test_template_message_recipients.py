"""
Tests for TemplateMessage recipients and blank messages.

See Issue #85 https://github.com/awdeorio/mailmerge/issues/85
"""
import textwrap
import pytest
from mailmerge import TemplateMessage, MailmergeError


def render_text(tmp_path, text, context):
    """Render template text with context."""
    template_path = tmp_path / "template.txt"
    template_path.write_text(textwrap.dedent(text), encoding="utf8")
    return TemplateMessage(template_path).render(context)


def test_wrapped_template(tmp_path):
    """A template wrapped in {% if %} keeps its headers when it renders."""
    text = """\
        {% if send == "yes" %}
        TO: to@test.com
        SUBJECT: Testing mailmerge
        FROM: from@test.com

        Hello world!
        {% endif %}
    """
    sender, recipients, message = render_text(tmp_path, text, {"send": "yes"})
    assert sender == "from@test.com"
    assert recipients == ["to@test.com"]
    assert message["subject"] == "Testing mailmerge"
    assert "Hello world!" in message.get_payload()


# The test brainstorm from the review of PR #177, one case per bullet.  Each
# template has only the headers its bullet names.  "{{blank}}" renders empty.
# The expected result is None for a skip, the recipients for a send, or part
# of the error message.
@pytest.mark.parametrize("text, expected", [
    # Whole message blank: skipped.
    pytest.param(
        "{% if blank %}TO: to@test.com\nFROM: from@test.com\n\nHello"
        "{% endif %}",
        None,
        id="whole-message-blank-skipped",
    ),
    # TO blank, CC filled: error.
    pytest.param(
        "TO: {{blank}}\nCC: cc@test.com\nFROM: from@test.com\n\nHello",
        "TO header is blank",
        id="to-blank-cc-filled-error",
    ),
    # TO blank, BCC filled: error.  (This is the BCC yourself example.)
    pytest.param(
        "TO: {{blank}}\nBCC: from@test.com\nFROM: from@test.com\n\nHello",
        "TO header is blank",
        id="to-blank-bcc-filled-error",
    ),
    # TO yourself, BCC filled: sent.  (This is how Gmail users hide
    # recipients.)
    pytest.param(
        "TO: from@test.com\nBCC: one@test.com, two@test.com\n"
        "FROM: from@test.com\n\nHello",
        ["from@test.com", "one@test.com", "two@test.com"],
        id="to-yourself-bcc-filled-sent",
    ),
    # TO yourself, BCC blank: error.
    pytest.param(
        "TO: from@test.com\nBCC: {{blank}}\nFROM: from@test.com\n\nHello",
        "BCC header is blank",
        id="to-yourself-bcc-blank-error",
    ),
    # Headers but no recipients: error.  (T0 with a zero is a typo for TO.)
    pytest.param(
        "T0: to@test.com\nFROM: from@test.com\n\nHello",
        "message has no recipients",
        id="headers-no-recipients-error",
    ),
])
def test_review_cases(tmp_path, text, expected):
    """Each case from the PR #177 review skips, sends or errors."""
    if isinstance(expected, str):
        with pytest.raises(MailmergeError, match=expected):
            render_text(tmp_path, text, {"blank": ""})
    elif expected is None:
        assert render_text(tmp_path, text, {"blank": ""}) == (None, [], None)
    else:
        _, recipients, message = render_text(tmp_path, text, {"blank": ""})
        assert recipients == expected
        assert "bcc" not in message


def test_unparseable_recipient(tmp_path):
    """A non-blank value that doesn't parse is not reported as blank.

    getaddresses() returns ('', '') for it, as it does for a blank value,
    which is why the blank check reads the header values.
    """
    render_text(tmp_path, """\
        TO: {{email}}
        FROM: from@test.com

        Hello world!
    """, {"email": "a@b.com,"})


@pytest.mark.parametrize("cc, expected", [
    ("c@test.com", ["to@test.com", "c@test.com"]),
    ("", ["to@test.com"]),
])
def test_optional_cc(tmp_path, cc, expected):
    """An {% if %} opened on the TO line adds CC without a blank line."""
    _, recipients, message = render_text(tmp_path, """\
        TO: to@test.com{% if cc %}
        CC: {{cc}}{% endif %}
        FROM: from@test.com

        Hello world!
    """, {"cc": cc})
    assert recipients == expected
    assert message["from"] == "from@test.com"


@pytest.mark.parametrize("text, body_start", [
    ("""\
        SUBJECT: Testing mailmerge
        {% if send == "yes" %}TO: to@test.com{% endif %}
        FROM: from@test.com

        Hello world!
    """, "FROM: from@test.com"),
    ("""\
        FROM: from@test.com
        {% if send == "yes" %}SUBJECT: Testing{% endif %}
        TO: to@test.com

        Hello world!
    """, "TO: to@test.com"),
])
def test_broken_header_block(tmp_path, text, body_start):
    """A blank line inside the headers produces a helpful error."""
    with pytest.raises(MailmergeError) as err:
        render_text(tmp_path, text, {"send": "no"})
    assert "a blank line ended the header block early" in str(err.value)
    assert body_start in str(err.value)


def test_no_from(tmp_path):
    """A message with recipients but no FROM produces an error."""
    with pytest.raises(MailmergeError) as err:
        render_text(tmp_path, """\
            TO: to@test.com

            Hello world!
        """, {})
    assert "message has no FROM header" in str(err.value)


def test_whitespace_only_message(tmp_path):
    """A render of only spaces, tabs and newlines is a blank message."""
    result = render_text(tmp_path, """\
        {% if send == "yes" %}
        TO: to@test.com
        FROM: from@test.com

        Hello world!
        {% endif %}
        {{pad}}
    """, {"send": "no", "pad": " \t \n  "})
    assert result == (None, [], None)


def test_text_outside_if(tmp_path):
    """Text outside the {% if %} makes the message non-blank: an error."""
    with pytest.raises(MailmergeError) as err:
        render_text(tmp_path, """\
            {% if send == "yes" %}
            TO: to@test.com
            FROM: from@test.com

            Hello world!
            {% endif %}
            Regards, the course team
        """, {"send": "no"})
    assert "message has no recipients" in str(err.value)


def test_repeated_header_one_blank(tmp_path):
    """A blank value in a repeated TO header is an error."""
    with pytest.raises(MailmergeError) as err:
        render_text(tmp_path, """\
            TO: to@test.com
            TO: {{email}}
            FROM: from@test.com

            Hello world!
        """, {"email": ""})
    assert "TO header is blank" in str(err.value)


def test_whitespace_recipient(tmp_path):
    """A value of only whitespace is blank."""
    with pytest.raises(MailmergeError) as err:
        render_text(tmp_path, """\
            TO: to@test.com
            CC: {{cc}}
            FROM: from@test.com

            Hello world!
        """, {"cc": "   "})
    assert "CC header is blank" in str(err.value)

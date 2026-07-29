"""Tests for configurable Markdown extensions."""

import pytest

from mailmerge import TemplateMessage


def _template(tmp_path):
    path = tmp_path / "template.txt"
    path.write_text(
        "TO: to@example.com\n"
        "SUBJECT: Markdown\n"
        "FROM: from@example.com\n"
        "CONTENT-TYPE: text/markdown\n\n"
        "```terraform\n"
        "resource \"example\" \"demo\" {\n"
        "  name = \"demo\"\n"
        "}\n"
        "```\n",
        encoding="utf8",
    )
    return path


def _html(message):
    return next(
        part for part in message.walk()
        if part.get_content_type() == "text/html"
    ).get_payload(decode=True).decode("utf8")


def test_fenced_code_is_configurable(tmp_path):
    """Fenced code is rendered only when the extension is enabled."""
    template = _template(tmp_path)

    _, _, default_message = TemplateMessage(template).render({})
    default_html = _html(default_message)
    assert "<pre>" not in default_html

    _, _, configured_message = TemplateMessage(
        template,
        markdown_extensions=["nl2br", "fenced_code"],
    ).render({})
    configured_html = _html(configured_message)
    assert "<pre><code class=\"language-terraform\">" in configured_html


def test_extension_configs_are_forwarded(tmp_path):
    """Extension configuration is passed to Python-Markdown."""
    pytest.importorskip("pygments")
    template = _template(tmp_path)
    _, _, message = TemplateMessage(
        template,
        markdown_extensions=["fenced_code", "codehilite"],
        extension_configs={
            "codehilite": {"noclasses": True, "guess_lang": False},
        },
    ).render({})
    html = _html(message)
    assert "class=\"codehilite\"" in html
    assert "style=\"" in html

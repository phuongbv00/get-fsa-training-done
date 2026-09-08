"""The Markdown subset the briefs use, and the page budget derived from them."""

from __future__ import annotations

import pytest

from fsa_trainer_skills.skills.assessment.core import budget, markdown

pypdf = pytest.importorskip("pypdf")


def test_inline_code_is_never_read_as_markup():
    assert markdown.render_inline("use `**not bold**` and **bold**") == (
        "use <code>**not bold**</code> and <strong>bold</strong>"
    )


def test_html_in_source_is_escaped():
    assert markdown.render_inline("List<String>") == "List&lt;String&gt;"


def test_nested_lists_and_tables_render():
    html = markdown.to_html_body("- one\n  1. inner\n- two\n\n| A | B |\n|---|--:|\n| x | 1 |\n")
    assert "<ul><li>one<ol><li>inner</li></ol></li><li>two</li></ul>" in html
    assert '<td style="text-align:right">1</td>' in html


def test_fenced_code_is_verbatim():
    html = markdown.to_html_body("```\n**raw** <b>\n```")
    assert "<pre><code>**raw** &lt;b&gt;</code></pre>" in html


def test_blockquote_banner_keeps_line_breaks():
    html = markdown.to_html_body("> **Code:** X\n> **Level:** FR")
    assert "<strong>Code:</strong> X<br><strong>Level:</strong> FR" in html


def test_page_budget_is_two_pages_per_hour_with_a_floor():
    assert budget.page_budget_for("> **Duration:** 2 hours") == (4, "Duration header")
    assert budget.page_budget_for("> **Duration:** 30 phút") == (2, "Duration header")
    assert budget.page_budget_for("> **Duration:** 5 days")[0] is None
    assert budget.page_budget_for("> **Duration:** 2 tuần")[0] is None
    assert budget.page_budget_for("no banner") == (None, "no Duration header")
    assert budget.page_budget_for("> **Duration:** 5 days", override=3) == (3, "--max-pages")

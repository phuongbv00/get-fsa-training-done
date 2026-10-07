"""Rendering a brief to PDF, and counting the pages it produced.

`render` used to shell out to headless Chrome, which resolved fonts from the
host. It now runs entirely in-process and embeds its own fonts, which is the
only way a `_vn` brief renders the same everywhere — so these assert the
property that motivated the change, not just that a file appeared.

Skipped wholesale when the managed environment's libraries are absent, which is
why they live here rather than beside the Markdown tests: those must never be
skipped for a reason that has nothing to do with them.
"""

from __future__ import annotations

import unicodedata

import pytest

from get_fsa_training_done.features.assessment.core import html as html_mod
from get_fsa_training_done.features.assessment.core import pdf as pdf_mod

pytest.importorskip("xhtml2pdf")
pypdf = pytest.importorskip("pypdf")

#
# `render` used to shell out to headless Chrome, which resolved fonts from the
# host. It now embeds them, which is the only way a `_vn` brief renders the same
# everywhere — so these assert the property that motivated the change, not just
# that a file appeared.


def vietnamese_letters() -> list[str]:
    """Every precomposed Vietnamese letter: 12 vowels x 6 tones, plus đ."""
    chars = set("đĐ")
    for base in "aăâeêioôơuưy":
        for tone in ("", "̀", "́", "̃", "̉", "̣"):
            for cased in (base, base.upper()):
                chars.add(unicodedata.normalize("NFC", cased + tone))
    return sorted(c for c in chars if len(c) == 1)


@pytest.mark.parametrize(
    "font",
    ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "RobotoMono-Regular.ttf", "RobotoMono-Bold.ttf"],
)
def test_every_embedded_font_covers_vietnamese(font):
    """The reason the mono face is Roboto and not DejaVu.

    DejaVu Sans Mono is missing all 46 double-diacritic Vietnamese letters, so
    Vietnamese inside a code span rendered as NUL with no error. Swapping either
    face for one with a narrower repertoire must fail here rather than silently
    degrading a `_vn` brief.
    """
    ttfonts = pytest.importorskip("reportlab.pdfbase.ttfonts")
    face = ttfonts.TTFont(font, str(pdf_mod.FONT_DIR / font))
    missing = [c for c in vietnamese_letters() if ord(c) not in face.face.charToGlyph]
    assert missing == []


def test_a_vietnamese_brief_survives_the_round_trip(tmp_path):
    """Prose, table cells, inline code and fenced code all carry diacritics."""
    source = (
        "# Đề bài kiểm tra\n\n"
        "Xây dựng lược đồ chuẩn hoá.\n\n"
        "| Tiêu chí | Điểm |\n|---|---|\n| Chuẩn hoá | 4 |\n\n"
        "```java\n// Đọc dữ liệu người dùng\nint x = 1;\n```\n\n"
        "Nộp bài dưới dạng `mã_số_sinh_viên.zip`.\n"
    )
    out = tmp_path / "brief.pdf"
    pdf_mod.render_html(html_mod.build_document(source, "Đề bài", lang="vi"), out)

    text = "\n".join(page.extract_text() for page in pypdf.PdfReader(str(out)).pages)
    for fragment in ("Đề bài", "lược đồ", "Tiêu chí", "Điểm", "Đọc dữ liệu người dùng", "mã_số"):
        assert fragment in text, f"{fragment!r} did not survive rendering"
    assert "\x00" not in text, "a glyph was missing from an embedded font"


def test_the_fonts_embed_wherever_the_command_runs(tmp_path, monkeypatch):
    """Run from a directory that does not contain the package.

    xhtml2pdf confines local reads to the working directory by default, and
    the installed fonts sit in site-packages. Every test used to run from the
    repository, which contains the fonts, so the 1.0.0 release shipped briefs
    that fell back to Helvetica — boxes for Vietnamese — on every real machine.
    """
    elsewhere = tmp_path / "project"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    out = tmp_path / "brief.pdf"
    pdf_mod.render_html(html_mod.build_document("# Đề bài\n\nNộp `bài`.\n", "t", lang="vi"), out)
    assert {"DejaVuSans", "RobotoMono-Regular"} <= pdf_mod.embedded_fonts(out)


def test_a_pdf_without_its_fonts_is_refused(tmp_path, monkeypatch):
    """Falling back to a built-in face still produces a PDF, so the renderer
    has to look for the faces it needs rather than trust a clean exit."""
    from get_fsa_training_done.errors import GftdError

    monkeypatch.setattr(pdf_mod, "REQUIRED_FONTS", ("NoSuchFace",))
    out = tmp_path / "brief.pdf"
    with pytest.raises(GftdError):
        pdf_mod.render_html(html_mod.build_document("# T\n", "t"), out)
    assert not out.exists()


def test_page_count_ignores_the_outline_tree(tmp_path):
    """`/Count` appears in the bookmark tree too, and the renderer emits one
    bookmark per heading. Counting those made a one-page brief report as many
    pages as it had headings, which could fail a budget it was well inside."""
    source = "# Title\n\n" + "\n\n".join(f"## Section {i}\n\nShort." for i in range(1, 9))
    out = tmp_path / "many_headings.pdf"
    reported = pdf_mod.render_html(html_mod.build_document(source, "T"), out)

    assert reported == len(pypdf.PdfReader(str(out)).pages) == 1


def test_a_long_brief_counts_every_page(tmp_path):
    source = "# Long\n\n" + "\n\n".join("Paragraph. " * 60 for _ in range(30))
    out = tmp_path / "long.pdf"
    reported = pdf_mod.render_html(html_mod.build_document(source, "L"), out)

    assert reported == len(pypdf.PdfReader(str(out)).pages) > 1

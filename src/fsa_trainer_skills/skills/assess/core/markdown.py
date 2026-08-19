"""Markdown to HTML, for the dialect the assessment workflows emit.

Headings, horizontal rules, blockquotes, fenced code, pipe tables, nested
ordered/unordered lists, and inline bold / code / links. That is the whole
surface a brief or rubric uses, and keeping the converter to that surface is
what lets the PDF pipeline stay dependency-free — which in turn is what lets it
run on an offline exam machine.

Not a CommonMark implementation, and not trying to be.
"""

from __future__ import annotations

import html
import re

_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+)`")
_MARKER = re.compile(r"^(?P<indent>\s*)(?P<marker>[-*]|\d+\.)\s+(?P<text>.*)$")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_RULE = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")
_FENCE = re.compile(r"^```(.*)$")
_FENCE_END = re.compile(r"^```\s*$")
_TABLE_SEPARATOR = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")
_PLACEHOLDER = re.compile(r"\x00(\d+)\x00")


def render_inline(text: str) -> str:
    """Inline Markdown to HTML, escaping everything else.

    Order matters. Code spans come out first so their contents are never read as
    bold or link markup, then the rest is escaped, then bold and links are
    applied to the now-safe text, then the code spans go back in.
    """
    stashed: list[str] = []

    def stash(match: re.Match) -> str:
        stashed.append("<code>" + html.escape(match.group(1)) + "</code>")
        return f"\x00{len(stashed) - 1}\x00"

    text = _CODE.sub(stash, text)
    text = html.escape(text)
    text = _BOLD.sub(lambda m: "<strong>" + m.group(1) + "</strong>", text)
    text = _LINK.sub(
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        text,
    )
    return _PLACEHOLDER.sub(lambda m: stashed[int(m.group(1))], text)


def _is_blank(line: str) -> bool:
    return line.strip() == ""


def _render_list(block: list[str]) -> str:
    """Render one contiguous list block into nested `<ul>`/`<ol>`."""
    roots: list[dict] = []
    stack: list[dict] = []  # open lists, outermost first

    def new_list(ordered: bool, indent: int) -> dict:
        return {"ordered": ordered, "indent": indent, "items": []}

    for line in block:
        match = _MARKER.match(line)
        if not match:
            # A wrapped continuation line belongs to the deepest open item.
            if stack and stack[-1]["items"]:
                stack[-1]["items"][-1]["text"] += " " + line.strip()
            continue

        indent = len(match.group("indent"))
        ordered = match.group("marker").endswith(".")
        item = {"text": match.group("text").strip(), "children": []}

        while stack and indent < stack[-1]["indent"]:
            stack.pop()

        if not stack:
            node = new_list(ordered, indent)
            stack.append(node)
            roots.append(node)
        elif indent > stack[-1]["indent"]:
            node = new_list(ordered, indent)
            stack[-1]["items"][-1]["children"].append(node)
            stack.append(node)
        elif ordered != stack[-1]["ordered"]:
            # Same depth, different marker type: a sibling list, not a nested one.
            stack.pop()
            node = new_list(ordered, indent)
            if stack:
                stack[-1]["items"][-1]["children"].append(node)
            else:
                roots.append(node)
            stack.append(node)

        stack[-1]["items"].append(item)

    def render(node: dict) -> str:
        tag = "ol" if node["ordered"] else "ul"
        parts = [f"<{tag}>"]
        for item in node["items"]:
            inner = render_inline(item["text"])
            for child in item["children"]:
                inner += render(child)
            parts.append(f"<li>{inner}</li>")
        parts.append(f"</{tag}>")
        return "".join(parts)

    return "".join(render(node) for node in roots)


def _cells(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [cell.strip() for cell in row.split("|")]


def _render_table(block: list[str]) -> str:
    header = _cells(block[0])
    aligns = []
    for spec in _cells(block[1]):
        left, right = spec.startswith(":"), spec.endswith(":")
        aligns.append("center" if left and right else "right" if right else "left")

    def align_at(index: int) -> str:
        return aligns[index] if index < len(aligns) else "left"

    parts = ["<table>", "<thead><tr>"]
    for index, cell in enumerate(header):
        parts.append(f'<th style="text-align:{align_at(index)}">{render_inline(cell)}</th>')
    parts.append("</tr></thead><tbody>")
    for row in block[2:]:
        if _is_blank(row):
            continue
        parts.append("<tr>")
        for index, cell in enumerate(_cells(row)):
            parts.append(f'<td style="text-align:{align_at(index)}">{render_inline(cell)}</td>')
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _starts_new_block(line: str) -> bool:
    return bool(
        _HEADING.match(line)
        or line.startswith("```")
        or _RULE.match(line)
        or line.lstrip().startswith(">")
        or _MARKER.match(line)
    )


def to_html_body(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]

        if _is_blank(line):
            i += 1
            continue

        if _FENCE.match(line):
            i += 1
            code: list[str] = []
            while i < n and not _FENCE_END.match(lines[i]):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            out.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        if _RULE.match(line):
            out.append("<hr>")
            i += 1
            continue

        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            out.append(f"<h{level}>{render_inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue

        if line.lstrip().startswith(">"):
            quoted: list[str] = []
            while i < n and lines[i].lstrip().startswith(">"):
                quoted.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            paragraphs: list[list[str]] = [[]]
            for quote_line in quoted:
                if _is_blank(quote_line):
                    paragraphs.append([])
                else:
                    paragraphs[-1].append(quote_line)
            body = "".join(
                "<p>" + "<br>".join(render_inline(x) for x in paragraph) + "</p>"
                for paragraph in paragraphs
                if paragraph
            )
            out.append(f"<blockquote>{body}</blockquote>")
            continue

        is_table = (
            "|" in line
            and i + 1 < n
            and _TABLE_SEPARATOR.match(lines[i + 1])
            and "-" in lines[i + 1]
        )
        if is_table:
            block = [line, lines[i + 1]]
            i += 2
            while i < n and "|" in lines[i] and not _is_blank(lines[i]):
                block.append(lines[i])
                i += 1
            out.append(_render_table(block))
            continue

        if _MARKER.match(line):
            block = []
            while i < n and not _is_blank(lines[i]):
                if not _MARKER.match(lines[i]) and not lines[i].startswith((" ", "\t")):
                    break
                block.append(lines[i])
                i += 1
            out.append(_render_list(block))
            continue

        paragraph_lines = []
        while i < n and not _is_blank(lines[i]):
            if _starts_new_block(lines[i]) and paragraph_lines:
                break
            if _starts_new_block(lines[i]) and not paragraph_lines:
                break
            paragraph_lines.append(lines[i].strip())
            i += 1
        if paragraph_lines:
            out.append(f"<p>{render_inline(' '.join(paragraph_lines))}</p>")
        else:  # pragma: no cover - defensive; every branch above consumes a line
            i += 1

    return "\n".join(out)


def document_title(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.*)$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else fallback

"""A small element tree read with the standard library's HTML parser.

Teaching material is HTML written to a narrow dialect — `references/material/
structure.md` — so the questions asked of it are structural: which slide uses
which layout, what a slot holds, whether a section opens with prose. A tree with
line numbers answers them; a browser-grade DOM would add a dependency for no
extra answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

#: Elements that never have content, so they never wait for a closing tag.
VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
#: Elements whose closing tag HTML lets an author leave out: closed implicitly
#: by the start tags below, or when an ancestor closes. Never reported unclosed.
IMPLIED_END = frozenset("p li dd dt tr td th thead tbody tfoot option".split())

#: Start tags that close an open `<p>`, as the HTML parsing rules define them.
CLOSES_P = frozenset(
    "address article aside blockquote details dialog div dl fieldset figcaption figure "
    "footer form h1 h2 h3 h4 h5 h6 header hgroup hr li main menu nav ol p pre section "
    "summary table ul dd dt".split()
)
#: Elements a `<p>` may still be open beneath when one of those arrives.
PHRASING = frozenset(
    "a abbr b bdi bdo cite code data dfn em i kbd mark q s samp small span strong sub sup "
    "time u var".split()
)
#: For a start tag that closes an open sibling: the siblings it closes, and the
#: elements that bound the search (a list item never closes one in an outer list).
CLOSES_SIBLING = {
    "li": ({"li"}, {"ul", "ol", "menu"}),
    "dd": ({"dd", "dt"}, {"dl"}),
    "dt": ({"dd", "dt"}, {"dl"}),
    "tr": ({"tr", "td", "th"}, {"table", "thead", "tbody", "tfoot"}),
    "td": ({"td", "th"}, {"tr", "table"}),
    "th": ({"td", "th"}, {"tr", "table"}),
    "thead": ({"thead", "tbody", "tfoot", "tr", "td", "th"}, {"table"}),
    "tbody": ({"thead", "tbody", "tfoot", "tr", "td", "th"}, {"table"}),
    "tfoot": ({"thead", "tbody", "tfoot", "tr", "td", "th"}, {"table"}),
    "option": ({"option"}, {"select", "datalist"}),
}


@dataclass
class Element:
    tag: str
    attrs: dict[str, str]
    line: int
    children: list[Element | str] = field(default_factory=list)
    parent: Element | None = field(default=None, repr=False)

    # --- Reading --------------------------------------------------------

    def get(self, name: str, default: str = "") -> str:
        return self.attrs.get(name, default)

    @property
    def classes(self) -> set[str]:
        return set(self.get("class").split())

    @property
    def elements(self) -> list[Element]:
        return [child for child in self.children if isinstance(child, Element)]

    def iter(self):
        """This element and every element under it, in document order."""
        yield self
        for child in self.elements:
            yield from child.iter()

    def find_all(self, tag: str | None = None, **attrs: str) -> list[Element]:
        """Descendants matching a tag and attribute values; `class_` matches a class."""
        wanted_class = attrs.pop("class_", None)
        found = []
        for element in self.iter():
            if element is self:
                continue
            if tag is not None and element.tag != tag:
                continue
            if wanted_class is not None and wanted_class not in element.classes:
                continue
            if any(element.get(key.replace("_", "-")) != value for key, value in attrs.items()):
                continue
            found.append(element)
        return found

    def find(self, tag: str | None = None, **attrs: str) -> Element | None:
        hits = self.find_all(tag, **attrs)
        return hits[0] if hits else None

    def text(self, *, keep_breaks: bool = False) -> str:
        """The element's text, whitespace collapsed.

        With `keep_breaks`, each `<br>` stays a newline: what a renderer lays
        out on separate lines, and what a fit estimate has to measure.
        """
        joined = "".join(self._walk_text())
        if not keep_breaks:
            return re.sub(r"\s+", " ", joined).strip()
        lines = (re.sub(r"[^\S\n]+", " ", line).strip() for line in joined.split("\n"))
        return "\n".join(lines).strip()

    def raw_text(self) -> str:
        """The element's text as written — for `<pre>`, where whitespace is content."""
        return "".join(self._walk_text())

    def _walk_text(self):
        for child in self.children:
            if isinstance(child, str):
                yield child
            elif child.tag == "br":
                yield "\n"
            else:
                yield from child._walk_text()

    def words(self) -> int:
        return len(self.text().split())

    def ancestor(self, tag: str) -> Element | None:
        node = self.parent
        while node is not None:
            if node.tag == tag:
                return node
            node = node.parent
        return None


@dataclass
class Document:
    path: Path
    source: str
    root: Element
    #: Problems the parser itself noticed: a stray closing tag, an unclosed one.
    problems: list[tuple[int, str]] = field(default_factory=list)

    @property
    def head(self) -> Element | None:
        return self.root.find("head")

    @property
    def body(self) -> Element:
        return self.root.find("body") or self.root

    def meta(self, name: str) -> str:
        for element in self.root.find_all("meta"):
            if element.get("name") == name:
                return element.get("content").strip()
        return ""

    @property
    def lang(self) -> str:
        """The language `<html lang>` declares, as `i18n` knows it; English if none."""
        from .i18n import language

        html = self.root.find("html")
        return language(html.get("lang") if html is not None else "")

    @property
    def title(self) -> str:
        element = self.root.find("title")
        return element.text() if element is not None else ""

    def ids(self) -> set[str]:
        return {element.get("id") for element in self.root.iter() if element.get("id")}


class _Builder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", {}, 1)
        self.stack = [self.root]
        self.problems: list[tuple[int, str]] = []

    def _close_implied(self, tag: str) -> None:
        """Pop what `tag`'s arrival closes, as a browser's parser would."""
        if tag in CLOSES_P:
            for depth in range(len(self.stack) - 1, 0, -1):
                name = self.stack[depth].tag
                if name == "p":
                    del self.stack[depth:]
                    break
                if name not in PHRASING:
                    break
        if tag in CLOSES_SIBLING:
            siblings, bounds = CLOSES_SIBLING[tag]
            for depth in range(len(self.stack) - 1, 0, -1):
                name = self.stack[depth].tag
                if name in siblings:
                    del self.stack[depth:]
                    break
                if name in bounds:
                    break

    def handle_starttag(self, tag: str, attrs) -> None:
        line = self.getpos()[0]
        self._close_implied(tag)
        element = Element(tag, {k: (v if v is not None else "") for k, v in attrs}, line)
        element.parent = self.stack[-1]
        self.stack[-1].children.append(element)
        if tag not in VOID:
            self.stack.append(element)

    def handle_startendtag(self, tag: str, attrs) -> None:
        line = self.getpos()[0]
        self._close_implied(tag)
        element = Element(tag, {k: (v if v is not None else "") for k, v in attrs}, line)
        element.parent = self.stack[-1]
        self.stack[-1].children.append(element)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID:
            return
        for depth in range(len(self.stack) - 1, 0, -1):
            if self.stack[depth].tag == tag:
                for unclosed in self.stack[depth + 1 :]:
                    if unclosed.tag not in IMPLIED_END:
                        self.problems.append((unclosed.line, f"<{unclosed.tag}> is never closed"))
                del self.stack[depth:]
                return
        self.problems.append((self.getpos()[0], f"</{tag}> closes nothing"))

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(data)


def serialize(node: Element | str) -> str:
    """HTML for a node, escaping text and attribute values the parser decoded."""
    import html

    if isinstance(node, str):
        return html.escape(node, quote=False)
    attrs = "".join(
        f' {name}="{html.escape(value, quote=True)}"' if value != "" else f" {name}"
        for name, value in node.attrs.items()
    )
    if node.tag in VOID:
        return f"<{node.tag}{attrs}>"
    inner = "".join(serialize(child) for child in node.children)
    return f"<{node.tag}{attrs}>{inner}</{node.tag}>"


def parse_text(text: str, path: Path | None = None) -> Document:
    builder = _Builder()
    builder.feed(text)
    builder.close()
    for unclosed in builder.stack[1:]:
        if unclosed.tag not in IMPLIED_END and unclosed.tag not in ("html", "body", "head"):
            builder.problems.append((unclosed.line, f"<{unclosed.tag}> is never closed"))
    return Document(
        path=path or Path("<string>"),
        source=text,
        root=builder.root,
        problems=builder.problems,
    )


def parse(path: Path) -> Document:
    from get_fsa_training_done.errors import UsageError

    if not path.is_file():
        raise UsageError(f"document not found: {path}")
    return parse_text(path.read_text(encoding="utf-8"), path)


__all__ = ["Document", "Element", "parse", "parse_text", "serialize"]

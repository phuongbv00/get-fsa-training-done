"""Rule bodies for teaching material: one document, a folder, and a slide deck."""

from __future__ import annotations

import math
import re
from pathlib import Path

from get_fsa_training_done.features.common.findings import Report

from . import assets, grammar, i18n
from . import deck as deck_mod
from . import layouts as L
from .dom import Document, Element

MIN_KNOWLEDGE_CHECK = 5

#: An erDiagram relationship: `A ||--o{ B : label`, or `..` for a
#: non-identifying one.
ER_RELATIONSHIP = re.compile(r"^\s*[\w-]+\s+[|}o][|o](?:--|\.\.)[|o][|{o]\s+[\w-]+\s*:\s*(.*)$")
CARDINALITY = re.compile(r"^\W*[1n]\s*-\s*[1n]\b", re.IGNORECASE)
#: Fixed colours: `style`/`classDef`/`linkStyle` with a colour, or a theme override.
FIXED_COLOUR = re.compile(
    r"^\s*(style|classDef|linkStyle)\b.*\b(fill|stroke|color)\s*:|themeVariables",
    re.IGNORECASE,
)


def _diagram_type(body: tuple[str, ...]) -> str:
    """The diagram keyword, after any `---` front matter, blank or `%%` lines."""
    in_front_matter = False
    for index, raw in enumerate(body):
        line = raw.strip()
        if line == "---" and (index == 0 or in_front_matter):
            in_front_matter = not in_front_matter
            continue
        if in_front_matter or not line or line.startswith("%%"):
            continue
        return line.split()[0]
    return ""


#: Elements that carry presentation rather than structure.
PRESENTATIONAL = ("style", "font", "center")
#: A deck runs between these many minutes per slide, by default.
MINUTES_PER_SLIDE = (1.5, 6.0)
#: Below this share of the template's size, a shrunk title or text slot is
#: reported: the deck's type stops looking like one deck.
MIN_FIT = 0.7


def check(document: Document, kind: grammar.Kind, report: Report, **options) -> None:
    where = document.path.name
    _well_formed(document, report, where)
    _declared_kind(document, kind, report, where)
    _theme(document, kind, report, where)
    export = options.pop("export", False)
    _code(document, report, where, export=export)
    _images(document, report, where, export=export)
    _links(document, report, where)
    _language(document, report, where)
    if kind is grammar.DECK:
        check_deck(document, report, **options)
    elif kind.parts:
        _parts(document, kind, report, where)
    if kind is grammar.NOTE:
        _note(document, report, where)
    if kind is grammar.LAB:
        _lab(document, report, where)


# --- Every document -------------------------------------------------------


def _well_formed(document: Document, report: Report, where: str) -> None:
    for line, problem in document.problems:
        report.error("MAT-D23", where, f"line {line}: {problem}")
    if document.root.find("html") is None or document.root.find("body") is None:
        report.error("MAT-D23", where, "no <html> or <body> element")


def _declared_kind(document: Document, kind: grammar.Kind, report: Report, where: str) -> None:
    declared = document.meta(grammar.META_KIND)
    if not declared:
        report.error("MAT-D21", where, f'no <meta name="{grammar.META_KIND}">')
    elif declared != kind.key:
        report.error(
            "MAT-D21",
            where,
            f"declares itself a {declared!r} but is named like a {kind.key!r}",
        )
    for name in kind.required_meta:
        if name != grammar.META_KIND and not document.meta(name):
            report.error("MAT-D21", where, f'no <meta name="{name}">')
    if not document.title:
        report.error("MAT-D21", where, "no <title>")
    body_classes = document.body.classes
    if kind.body_class not in body_classes:
        report.error("MAT-D21", where, f'<body> should carry class="{kind.body_class}"')


def _theme(document: Document, kind: grammar.Kind, report: Report, where: str) -> None:
    sheets = [
        link.get("href")
        for link in document.root.find_all("link")
        if "stylesheet" in link.get("rel").split()
    ]
    if not any(href.endswith(grammar.THEME_CSS) for href in sheets):
        report.error("MAT-D22", where, f"does not link {grammar.THEME_CSS}")
    for href in sheets:
        if not href.endswith(grammar.THEME_CSS) and not href.startswith(grammar.THEME_DIR):
            report.error("MAT-D22", where, f"links a stylesheet outside the theme: {href}")
    for element in document.root.iter():
        if element.get("style"):
            report.error("MAT-D22", where, f"line {element.line}: inline style on <{element.tag}>")
        if element.tag in PRESENTATIONAL:
            report.error("MAT-D22", where, f"line {element.line}: <{element.tag}> element")
    if kind is grammar.DECK:
        scripts = [script.get("src") for script in document.root.find_all("script")]
        if not any(src.endswith(grammar.DECK_JS) for src in scripts):
            report.error("MAT-D22", where, f"a deck loads {grammar.DECK_JS}")


def _code(document: Document, report: Report, where: str, *, export: bool) -> None:
    for pre in document.root.find_all("pre"):
        if "mermaid" in pre.classes:
            _diagram(pre, report, where, export=export)
            continue
        code = pre.find("code")
        classes = " ".join(sorted((code.classes if code is not None else set()) | pre.classes))
        match = grammar.CODE_LANGUAGE.search(classes)
        if match is None:
            report.error(
                "MAT-D10",
                where,
                f'line {pre.line}: a code block has no language — <code class="language-…">',
            )
        elif match.group(1).lower() not in grammar.CODE_LANGUAGES:
            report.warn("MAT-D11", where, f"line {pre.line}: unknown language {match.group(1)!r}")


def _diagram(pre: Element, report: Report, where: str, *, export: bool) -> None:
    body = tuple(pre.raw_text().splitlines())
    is_er = _diagram_type(body) == "erDiagram"
    for offset, line in enumerate(body):
        number = pre.line + offset
        relationship = ER_RELATIONSHIP.match(line) if is_er else None
        if relationship and not CARDINALITY.match(relationship.group(1).strip("\"' ")):
            report.warn(
                "MAT-D19",
                where,
                f'line {number}: label the relationship with its cardinality, e.g. "1-n places"',
            )
        if FIXED_COLOUR.search(line):
            report.warn("MAT-D20", where, f"line {number}: colour fixed in the diagram")
    figure = pre.ancestor("figure")
    if export and (figure is None or figure.find("img") is None):
        report.warn(
            "MAT-X01",
            where,
            f"line {pre.line}: no rendered <img> beside the diagram, so exports show its source",
        )


def _images(document: Document, report: Report, where: str, *, export: bool) -> None:
    for image in document.root.find_all("img"):
        if not image.get("alt").strip():
            report.warn("MAT-D24", where, f"line {image.line}: <img> has no alt text")
        src = image.get("src")
        path = assets.resolve(document.path, src)
        if path is not None and not path.exists():
            report.error("MAT-D12", where, f"line {image.line}: {src} does not exist")
            continue
        if export and src and not assets.is_external(src):
            _, problem = assets.embeddable(document.path, src)
            if problem:
                report.warn("MAT-X03", where, f"line {image.line}: {problem}")


def _links(document: Document, report: Report, where: str) -> None:
    from . import dom

    own_ids = document.ids()
    for anchor in document.root.find_all("a"):
        href = anchor.get("href")
        if not href or assets.is_external(href):
            continue
        target, fragment = assets.split(href)
        if target:
            resolved = assets.resolve(document.path, href)
            if not resolved.exists():
                report.error("MAT-D12", where, f"line {anchor.line}: {target} does not exist")
                continue
            ids = dom.parse(resolved).ids() if resolved.suffix == ".html" else None
        else:
            ids = own_ids
        if fragment and ids is not None and fragment not in ids:
            report.error(
                "MAT-D13",
                where,
                f"line {anchor.line}: #{fragment} is not an id in {target or where}",
            )


def _language(document: Document, report: Report, where: str) -> None:
    """The text is in the language `<html lang>` declares."""
    hits = grammar.VIETNAMESE.findall(document.body.text())
    if grammar.is_translation(where) and document.lang != "vi":
        report.warn(
            "MAT-D16",
            where,
            f'a {grammar.TRANSLATION_SUFFIX} translation declares <html lang="vi">',
        )
    elif hits and document.lang != "vi":
        report.warn(
            "MAT-D16",
            where,
            f"contains Vietnamese ({len(hits)} letters) but declares lang "
            f'"{document.lang}": declare <html lang="vi">, or move it to a '
            f"{grammar.TRANSLATION_SUFFIX} translation",
        )


# --- Long-form documents --------------------------------------------------


def parts_of(document: Document) -> list[Element]:
    return [section for section in document.body.find_all("section") if section.get("data-part")]


def _parts(document: Document, kind: grammar.Kind, report: Report, where: str) -> None:
    found = parts_of(document)
    keys = [section.get("data-part") for section in found]
    known = [part.key for part in kind.parts]

    for section in found:
        key = section.get("data-part")
        if key not in known:
            report.error(
                "MAT-D29",
                where,
                f"line {section.line}: unknown part {key!r}; a {kind.key} has " + ", ".join(known),
            )
        elif not kind.part(key).repeatable and keys.count(key) > 1:
            report.error("MAT-D29", where, f"line {section.line}: part {key!r} appears twice")
        if section.find("h2") is None:
            report.error("MAT-D29", where, f"line {section.line}: part {key!r} has no <h2>")

    for part in kind.parts:
        if part.required and part.key not in keys:
            rule = "MAT-D06" if part.key == "objectives" else "MAT-D29"
            if part.key in ("knowledge-check", "further-reading"):
                rule = "MAT-D08"
            report.error(rule, where, f"no {part.key!r} part ({part.heading})")

    order = [known.index(key) for key in keys if key in known]
    if order != sorted(order):
        report.error(
            "MAT-D29",
            where,
            "parts are out of order: "
            + ", ".join(key for n, key in enumerate(keys) if not n or keys[n - 1] != key)
            + "; expected "
            + ", ".join(key for key in known if key in keys),
        )

    if keys and "objectives" in known and keys[0] != "objectives":
        report.error("MAT-D06", where, f"the first part is {keys[0]!r}, not 'objectives'")

    objectives = _part(found, "objectives")
    if objectives is not None:
        opening = next((p.text() for p in objectives.find_all("p")), "")
        if not i18n.opens_objectives(opening):
            expected = (
                "Sau bài học này, học viên có thể:"
                if document.lang == "vi"
                else ("After this unit, learners can:")
            )
            report.error(
                "MAT-D06",
                where,
                f"the objectives open {opening[:48]!r}; expected {expected!r}",
            )
        _objective_codes(document, objectives, report, where)


def _part(found: list[Element], key: str) -> Element | None:
    for section in found:
        if section.get("data-part") == key:
            return section
    return None


def top_items(element: Element) -> list[Element]:
    """The items of the first list in an element, not those of lists nested in them."""
    for candidate in element.iter():
        if candidate.tag in ("ul", "ol"):
            return [child for child in candidate.elements if child.tag == "li"]
    return []


def _objective_codes(
    document: Document, objectives: Element, report: Report, where: str
) -> set[str]:
    items = top_items(objectives)
    if not items:
        report.error("MAT-D06", where, "the objectives part has no list")
    cited = set()
    for item in items:
        code = item.get("data-objective")
        if not code:
            report.error(
                "MAT-D31",
                where,
                f"line {item.line}: objective {item.text()[:40]!r} has no data-objective",
            )
        cited.update(code.split())
    declared = set(document.meta(grammar.META_OBJECTIVES).split())
    if declared and cited and declared - cited:
        report.error(
            "MAT-D31",
            where,
            "fsa:objectives lists "
            + ", ".join(sorted(declared - cited))
            + " but no objective cites it",
        )
    return cited


def _note(document: Document, report: Report, where: str) -> None:
    found = parts_of(document)
    objectives = _part(found, "objectives")
    codes = {
        code
        for item in (top_items(objectives) if objectives is not None else [])
        for code in item.get("data-objective").split()
    }

    check_part = _part(found, "knowledge-check")
    if check_part is not None:
        questions = top_items(check_part)
        if len(questions) < MIN_KNOWLEDGE_CHECK:
            report.warn(
                "MAT-D09",
                where,
                f"the knowledge check asks {len(questions)} question(s); "
                f"{MIN_KNOWLEDGE_CHECK} is the floor",
            )
        tested = set()
        for number, question in enumerate(questions, 1):
            if question.find("details") is None:
                report.error("MAT-D25", where, f"knowledge-check question {number} has no answer")
            tested.update(question.get("data-objective").split())
        untested = sorted(codes - tested)
        if untested:
            report.warn(
                "MAT-D26",
                where,
                "no knowledge-check question tests " + ", ".join(untested),
            )

    for section in found:
        if section.get("data-part") != "concept":
            continue
        heading = section.find("h2")
        name = heading.text() if heading is not None else f"line {section.line}"
        _explains_first(section, name, report, where)
        try_it = section.find(class_="try-it")
        if try_it is None:
            report.warn("MAT-D28", where, f"concept {name!r} has nothing to try")
        elif try_it.find("details") is None:
            report.warn("MAT-D28", where, f"concept {name!r}: the try-it has no answer")


def _explains_first(section: Element, name: str, report: Report, where: str) -> None:
    """The first content after the heading is prose, not an example."""
    for child in section.elements:
        if child.tag in ("h2", "h3"):
            continue
        if child.tag in ("pre", "figure", "table", "img"):
            report.warn("MAT-D27", where, f"concept {name!r} shows <{child.tag}> before explaining")
        return


def _lab(document: Document, report: Report, where: str) -> None:
    found = parts_of(document)
    steps = _part(found, "steps")
    if steps is not None:
        ordered = steps.find("ol")
        items = [child for child in ordered.elements if child.tag == "li"] if ordered else []
        if not items:
            report.error("MAT-D17", where, "the steps are not an ordered list")
        for number, item in enumerate(items, 1):
            if item.find(class_="expected") is None:
                report.warn("MAT-D30", where, f"step {number} does not say what to expect")
    acceptance = _part(found, "acceptance")
    if acceptance is not None:
        checklist = acceptance.find("ul", class_="checklist")
        if checklist is None or not top_items(checklist):
            report.error("MAT-D17", where, 'the acceptance part has no <ul class="checklist">')
    minutes = document.meta(grammar.META_MINUTES)
    if not minutes.isdigit():
        report.warn("MAT-D18", where, "fsa:minutes is not a number of minutes")


# --- A slide deck ---------------------------------------------------------


def check_deck(
    document: Document,
    report: Report,
    *,
    minutes_per_slide: tuple[float, float] = MINUTES_PER_SLIDE,
    min_fit: float = MIN_FIT,
) -> list[deck_mod.Slide]:
    where = document.path.name
    slides = deck_mod.read(document)
    if not slides:
        report.error("MAT-S01", where, 'no <section class="slide">')
        return slides

    for slide in slides:
        _slide(slide, report, where, min_fit)
    _order(slides, report, where)
    _deck_objectives(document, slides, report, where)
    _checks_per_section(slides, report, where)
    _slide_budget(document, slides, report, where, minutes_per_slide)
    return slides


def _slide(slide: deck_mod.Slide, report: Report, where: str, min_fit: float = MIN_FIT) -> None:
    if slide.layout is None:
        report.error(
            "MAT-S02",
            where,
            f"{slide.where()}: unknown layout {slide.layout_name!r}; "
            "see references/material/layouts.md",
        )
        return
    for name in slide.unknown_slots:
        report.error("MAT-S02", where, f"{slide.where()}: {slide.layout.name} has no slot {name!r}")
    for element in slide.stray:
        report.error(
            "MAT-S02",
            where,
            f"{slide.where()}: <{element.tag}> on line {element.line} is outside any slot",
        )
    for name in slide.layout.required:
        if name not in slide.slots or not (
            slide.slots[name].text()
            or slide.slots[name].tag == "img"
            or slide.slots[name].find("img")
        ):
            report.error("MAT-S03", where, f"{slide.where()}: slot {name!r} is empty")

    for name, element in slide.slots.items():
        spec = slide.layout.slot(name)
        if spec is None:
            continue
        _slot_limits(slide, spec, element, report, where, min_fit)

    if slide.role_kind in (L.CONTENT, L.OBJECTIVES):
        words = slide.notes.words() if slide.notes is not None else 0
        if words < L.MIN_NOTE_WORDS:
            report.warn(
                "MAT-S06",
                where,
                f"{slide.where()}: {words} word(s) of speaker notes; "
                f"{L.MIN_NOTE_WORDS} is the floor",
            )
    if slide.role == "check":
        body = " ".join(element.text() for element in slide.slots.values())
        if not any(element.find("details") for element in slide.slots.values()) or not body:
            report.warn(
                "MAT-S07", where, f"{slide.where()}: the check slide has no <details> answer"
            )


def _slot_limits(
    slide: deck_mod.Slide,
    spec: L.Slot,
    element: Element,
    report: Report,
    where: str,
    min_fit: float = MIN_FIT,
) -> None:
    if spec.kind in (L.TITLE, L.TEXT):
        block = [
            child.tag for child in element.elements if child.tag in ("ul", "ol", "pre", "table")
        ]
        if block:
            report.error(
                "MAT-S02",
                where,
                f"{slide.where()}: slot {spec.name!r} holds text only, not <{block[0]}>",
            )
        # As the browser and the exporters lay it out: a `<br>` is a new line.
        text = element.text(keep_breaks=True)
        if slide.role_kind == L.SECTION and spec.name == "title":
            text = "00.\n" + text
        if L.overflows(spec, text):
            report.warn(
                "MAT-S08",
                where,
                f"{slide.where()}: slot {spec.name!r} does not fit even shrunk to "
                f"{min(L.FIT_SCALES):.0%}; shorten it",
            )
        elif (scale := L.fit_scale(spec, text)) < min_fit:
            report.warn(
                "MAT-S10",
                where,
                f"{slide.where()}: slot {spec.name!r} shrinks to {scale:.0%} of the "
                f"template's {spec.size}pt; shorten it to keep the deck's type even",
            )
    elif spec.kind == L.PICTURE:
        if element.tag != "img" and element.find("img") is None:
            report.error("MAT-S02", where, f"{slide.where()}: slot {spec.name!r} holds an <img>")
    else:
        items = top_items(element)
        if spec.max_items and len(items) > spec.max_items:
            report.warn(
                "MAT-S08",
                where,
                f"{slide.where()}: slot {spec.name!r} has {len(items)} items; {spec.max_items} fit",
            )
        for pre in element.find_all("pre"):
            if "mermaid" in pre.classes:
                continue
            code = pre.raw_text().strip("\n").splitlines()
            widest = max((len(line.expandtabs(4)) for line in code), default=0)
            room = L.code_columns(spec)
            if widest > room:
                report.warn(
                    "MAT-S08",
                    where,
                    f"{slide.where()}: a line of code is {widest} characters; "
                    f"{room} fit across slot {spec.name!r}",
                )
            lines = len(code)
            if lines > L.MAX_CODE_LINES:
                report.warn(
                    "MAT-S08",
                    where,
                    f"{slide.where()}: {lines} lines of code; {L.MAX_CODE_LINES} fit",
                )


def _order(slides: list[deck_mod.Slide], report: Report, where: str) -> None:
    roles = [slide.role_kind for slide in slides if slide.layout is not None]
    expected = "cover, (toc), objectives, sections, summary, closing"

    def fail(message: str) -> None:
        report.error("MAT-S01", where, f"{message}; expected {expected}")

    if not roles:
        return
    if roles[0] != L.COVER:
        fail(f"the first slide is {roles[0]!r}")
    position = 1
    if position < len(roles) and roles[position] == L.TOC:
        position += 1
    if position >= len(roles) or roles[position] != L.OBJECTIVES:
        fail("Lesson Objectives does not follow the cover")
    else:
        position += 1
    if position < len(roles) and roles[position] != L.SECTION:
        fail(f"slide {position + 1} comes before the first section cover")
    for index, role in enumerate(roles):
        if role in (L.COVER, L.TOC, L.OBJECTIVES) and index > 2:
            fail(f"slide {index + 1} is a second {role!r}")
    if L.SUMMARY not in roles:
        fail("no Lesson Summary")
    elif roles[-2:] != [L.SUMMARY, L.CLOSING]:
        fail("the deck does not end with Lesson Summary, then the closing slide")
    if roles.count(L.SUMMARY) > 1 or roles.count(L.CLOSING) > 1:
        fail("more than one summary or closing slide")
    if L.SECTION not in roles:
        fail("no section cover")
    for cover, inside in deck_mod.sections(slides):
        if not inside:
            report.error(
                "MAT-S01", where, f"{cover.where()}: the section {cover.title()!r} is empty"
            )


def _codes_of(slide: deck_mod.Slide) -> set[str]:
    return {
        code
        for item in deck_mod.objective_items(slide)
        for code in item.get("data-objective").split()
    }


def _deck_objectives(
    document: Document, slides: list[deck_mod.Slide], report: Report, where: str
) -> None:
    declared = set(document.meta(grammar.META_OBJECTIVES).split())
    objectives = [slide for slide in slides if slide.role_kind == L.OBJECTIVES]
    summaries = [slide for slide in slides if slide.role_kind == L.SUMMARY]
    stated: set[str] = set()
    if objectives:
        slide = objectives[0]
        body = slide.slots.get("body")
        items = top_items(body) if body is not None else []
        for item in items:
            if not item.get("data-objective"):
                report.error(
                    "MAT-S04",
                    where,
                    f"{slide.where()}: objective {item.text()[:40]!r} has no data-objective",
                )
        stated = _codes_of(slide)
        missing = sorted(declared - stated)
        if missing:
            report.error(
                "MAT-S04", where, f"{slide.where()}: no objective states " + ", ".join(missing)
            )
    if summaries:
        slide = summaries[0]
        closed = _codes_of(slide)
        open_ = sorted((stated or declared) - closed)
        if open_:
            report.error(
                "MAT-S05", where, f"{slide.where()}: the summary never closes " + ", ".join(open_)
            )
        stray = sorted(closed - (stated or declared))
        if stray:
            report.error(
                "MAT-S05",
                where,
                f"{slide.where()}: the summary cites " + ", ".join(stray) + ", not an objective",
            )


def _checks_per_section(slides: list[deck_mod.Slide], report: Report, where: str) -> None:
    for cover, inside in deck_mod.sections(slides):
        if not any(slide.role == "check" for slide in inside):
            report.warn("MAT-S07", where, f"section {cover.title()!r} has no check slide")


def _slide_budget(
    document: Document,
    slides: list[deck_mod.Slide],
    report: Report,
    where: str,
    minutes_per_slide: tuple[float, float],
) -> None:
    minutes = document.meta(grammar.META_MINUTES)
    if not minutes.isdigit() or not int(minutes):
        return
    fastest, slowest = minutes_per_slide
    low = math.floor(int(minutes) / slowest)
    high = math.ceil(int(minutes) / fastest)
    if not low <= len(slides) <= high:
        report.warn(
            "MAT-S09",
            where,
            f"{len(slides)} slides for {minutes} minutes; {low}–{high} fit at "
            f"{fastest:g}–{slowest:g} minutes a slide",
        )


def check_folder(paths: list[Path], report: Report) -> None:
    """Index rules across a folder, per kind: a deck and its note share an index."""
    by_kind: dict[str, dict[str, list[str]]] = {}
    for path in paths:
        kind = grammar.kind_for(path.name)
        if kind not in (grammar.DECK, grammar.NOTE) or grammar.is_translation(path.name):
            continue
        match = kind.filename.match(path.name)
        by_kind.setdefault(kind.key, {}).setdefault(match.group(1) + match.group(2), []).append(
            path.name
        )
    for indexes in by_kind.values():
        for index, names in sorted(indexes.items()):
            if len(names) > 1:
                report.error(
                    "MAT-D02",
                    names[0],
                    f"index {index} is claimed by {len(names)} files: " + ", ".join(sorted(names)),
                )
    notes = by_kind.get("note", {})
    numeric = sorted(
        int(index[:2])
        for index in notes
        if index[:2] not in (grammar.HANDBOOK_INDEX, grammar.APPENDIX_INDEX)
    )
    if numeric:
        missing = [n for n in range(1, max(numeric) + 1) if n not in numeric]
        if missing:
            report.warn(
                "MAT-D03",
                paths[0].parent.name or ".",
                "no note at index " + ", ".join(f"{n:02d}" for n in missing),
            )


__all__ = ["MINUTES_PER_SLIDE", "check", "check_deck", "check_folder", "parts_of", "top_items"]

"""Rule bodies for one document, and for a folder of them."""

from __future__ import annotations

import re
from pathlib import Path

from fsa_trainer_skills.findings import Report

from . import grammar, notes

FRONT_MATTER = re.compile(r"\A---\s*$", re.MULTILINE)
MIN_KNOWLEDGE_CHECK = 5


def check_folder(paths: list[Path], report: Report) -> None:
    """Rules about a set of documents rather than any one of them."""
    indexes: dict[str, list[str]] = {}
    for path in paths:
        match = grammar.NOTE_FILENAME.match(path.name)
        if match:
            indexes.setdefault(match.group(1) + match.group(2), []).append(path.name)

    for index, names in sorted(indexes.items()):
        if len(names) > 1:
            report.error(
                "MAT-D02",
                names[0],
                f"index {index} is claimed by {len(names)} files: " + ", ".join(sorted(names)),
            )

    numeric = sorted(
        int(index[:2])
        for index in indexes
        if index[:2] not in (grammar.HANDBOOK_INDEX, grammar.APPENDIX_INDEX)
    )
    if numeric:
        expected = list(range(1, max(numeric) + 1))
        missing = [n for n in expected if n not in numeric]
        if missing:
            report.warn(
                "MAT-D03",
                paths[0].parent.name or ".",
                "no note at index " + ", ".join(f"{n:02d}" for n in missing),
            )


def check(
    note: notes.Note,
    report: Report,
    *,
    template: grammar.Template,
    known_files: set[str] | None = None,
) -> None:
    where = note.path.name
    _filename(note, report, where, template)
    _heading(note, report, where)
    _sections(note, report, where, template)
    _fences(note, report, where)
    _links(note, report, where, known_files)
    _language(note, report, where)
    if template is grammar.LAB:
        _lab(note, report, where)


def _filename(note: notes.Note, report: Report, where: str, template: grammar.Template) -> None:
    if template is grammar.LAB:
        if not grammar.LAB_FILENAME.match(where):
            report.error("MAT-D01", where, "a lab guide is named `<subject>_lab_NN.md`")
        return
    stem = where[: -len(".md")] if where.endswith(".md") else where
    if stem.endswith(grammar.TRANSLATION_SUFFIX):
        stem = stem[: -len(grammar.TRANSLATION_SUFFIX)]
    if not grammar.NOTE_FILENAME.match(f"{stem}.md"):
        report.error(
            "MAT-D01",
            where,
            "a note is named `NN_Topic_Name.md`, two digits then a title in Title_Case",
        )


def _heading(note: notes.Note, report: Report, where: str) -> None:
    if FRONT_MATTER.match(note.text):
        report.error("MAT-D05", where, "the file opens with YAML front matter")
    tops = [heading for heading in note.headings if heading.level == 1]
    if not tops:
        report.error("MAT-D04", where, "no top-level heading")
        return
    if tops[0].line != 1:
        report.error("MAT-D04", where, f"the title is on line {tops[0].line}, not line 1")
    if len(tops) > 1:
        lines = ", ".join(str(heading.line) for heading in tops[1:])
        report.error("MAT-D04", where, f"more than one top-level heading (also on line {lines})")


def _sections(note: notes.Note, report: Report, where: str, template: grammar.Template) -> None:
    if template.numbered_sections:
        numbers = [heading.number for heading in note.sections if heading.number is not None]
        if numbers:
            expected = list(range(1, len(numbers) + 1))
            if numbers != expected:
                report.error(
                    "MAT-D07",
                    where,
                    f"numbered sections read {numbers}, expected {expected}",
                )

    for index, slot in enumerate(template.slots):
        heading = note.section_named(slot.names)
        if heading is None:
            if slot.required:
                report.error("MAT-D08" if index else "MAT-D06", where, f"no `{slot.label}` section")
            continue
        if slot.opening is not None:
            opening = notes.first_prose(note.body_of(heading))
            if not slot.opening.match(opening):
                report.error(
                    "MAT-D06",
                    where,
                    f"`{heading.text}` opens {opening[:48]!r}; expected "
                    f"{slot.opening.pattern.lstrip('^')!r}",
                )
        if slot.names[0] in ("Knowledge Check", "Quick Check"):
            questions = notes.numbered_items(note.body_of(heading))
            if len(questions) < MIN_KNOWLEDGE_CHECK:
                report.warn(
                    "MAT-D09",
                    where,
                    f"`{heading.text}` asks {len(questions)} question(s); "
                    f"{MIN_KNOWLEDGE_CHECK} is the floor",
                )
        if slot.names[0] == "Self-check checklist":
            if not notes.task_items(note.body_of(heading)):
                report.error("MAT-D15", where, f"`{heading.text}` has no `- [ ]` items to tick off")

    if template.footer is not None:
        tail = [line for line in note.lines if line.strip()]
        if not tail or not template.footer.match(tail[-1].strip()):
            report.error("MAT-D14", where, "no `Next:` or `Review:` line at the end")


def _fences(note: notes.Note, report: Report, where: str) -> None:
    for fence in note.fences:
        if not fence.language:
            report.error("MAT-D10", where, f"line {fence.line}: fenced block has no language")
        elif not notes.known_language(fence.language):
            report.warn(
                "MAT-D11", where, f"line {fence.line}: unknown fence language {fence.language!r}"
            )


def _links(note: notes.Note, report: Report, where: str, known_files: set[str] | None) -> None:
    for href, line in note.links:
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target, _, anchor = href.partition("#")
        if target:
            resolved = (note.path.parent / target).resolve()
            if not resolved.exists():
                report.error("MAT-D12", where, f"line {line}: {target} does not exist")
                continue
            slugs = notes.parse(resolved).slugs() if resolved.suffix == ".md" else set()
        else:
            slugs = note.slugs()
        if anchor and anchor.lower() not in slugs:
            report.error(
                "MAT-D13",
                where,
                f"line {line}: #{anchor} is not a heading in {target or where}",
            )
    del known_files


def _language(note: notes.Note, report: Report, where: str) -> None:
    stem = where[: -len(".md")] if where.endswith(".md") else where
    if stem.endswith(grammar.TRANSLATION_SUFFIX):
        return
    hits = grammar.VIETNAMESE.findall(note.text)
    if hits:
        report.warn(
            "MAT-D16",
            where,
            f"contains Vietnamese ({len(hits)} letters); a translation is a separate "
            f"file ending {grammar.TRANSLATION_SUFFIX}",
        )


def _lab(note: notes.Note, report: Report, where: str) -> None:
    steps = note.section_named(("Steps",))
    if steps is not None and not notes.numbered_items(note.body_of(steps)):
        report.error("MAT-D17", where, "`Steps` is not an ordered list")
    acceptance = note.section_named(("Acceptance", "Done when"))
    if acceptance is not None and not notes.task_items(note.body_of(acceptance)):
        report.error("MAT-D17", where, "the acceptance list has no `- [ ]` items")
    if not grammar.LAB_DURATION.search(note.text):
        report.warn("MAT-D18", where, "no `**Duration:** N min` line")


__all__ = ["MIN_KNOWLEDGE_CHECK", "check", "check_folder"]

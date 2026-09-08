"""Topic-level rules: one syllabus and the session plan beside it."""

from __future__ import annotations

import re

from fsa_trainer_skills.findings import Report

from .. import contracts as contracts_mod
from ..schedule import DELIVERY_TYPES, SCHEDULE_HEADER, TRAINING_FORMAT
from ..syllabus import FORBIDDEN_FOOTER, FORBIDDEN_SECTIONS, PASS_CRITERIA, Syllabus
from . import as_number

#: Rounding slack on a percentage share. The shares are written to two decimal
#: places, so a hundredth either way is presentation, not disagreement.
SHARE_TOLERANCE = 0.011

OBJECTIVE_CODE = re.compile(r"\b[A-Z][A-Z0-9]*-[A-Z]\d+\b")


def check(
    syllabus: Syllabus,
    schedule,
    report: Report,
    *,
    minutes_per_day: int,
    max_sessions_per_chapter: float = 2,
    pass_mark: int = 6,
    creator: dict | None = None,
    item_patterns: dict[str, str] | None = None,
) -> None:
    where = syllabus.path.name
    _identity(syllabus, schedule, report, where)
    _forbidden_sections(syllabus, report, where)
    _substance(syllabus, report, where)
    _authorship(syllabus, report, where, creator=creator or {})

    if schedule is None:
        return
    if list(schedule.headers) != list(SCHEDULE_HEADER):
        report.error("PRG-S01", schedule.path.name, "header does not match the fixed nine columns")
        return

    rows = schedule.rows
    _rows(rows, report, schedule.path.name)
    minutes = _minutes(syllabus, rows, report, minutes_per_day)
    _sessions(rows, report, schedule.path.name, minutes_per_day, max_sessions_per_chapter)
    if minutes:
        _shares(syllabus, rows, minutes, report, where)
    _assessments(syllabus, rows, report, where, pass_mark=pass_mark, item_patterns=item_patterns)
    _objectives(syllabus, rows, report, schedule.path.name)


def _identity(syllabus: Syllabus, schedule, report: Report, where: str) -> None:
    stem = syllabus.path.stem
    from_name = stem[: -len("_Syllabus")] if stem.endswith("_Syllabus") else stem
    if not syllabus.code:
        report.error("PRG-S02", where, "no '# CODE — Title' heading found")
        return
    if syllabus.code != from_name:
        report.error(
            "PRG-S02", where, f"heading says {syllabus.code} but the filename says {from_name}"
        )
    if syllabus.fields.get(3) and syllabus.fields[3] != syllabus.code:
        report.error(
            "PRG-S02",
            where,
            f"Topic Code field is {syllabus.fields[3]} but the heading says {syllabus.code}",
        )
    if syllabus.fields.get(2) and syllabus.fields[2] != syllabus.title:
        report.error(
            "PRG-S02",
            where,
            f"Topic Name field is {syllabus.fields[2]!r} but the heading says {syllabus.title!r}",
        )


def _forbidden_sections(syllabus: Syllabus, report: Report, where: str) -> None:
    for heading in FORBIDDEN_SECTIONS:
        if heading in syllabus.text:
            report.error(
                "PRG-S15",
                where,
                f"{heading} has no cell in the workbook and is dropped on export",
            )
    if FORBIDDEN_FOOTER.search(syllabus.text):
        report.error("PRG-S15", where, "the 'Schedule detail:' footer has no cell in the workbook")


def _substance(syllabus: Syllabus, report: Report, where: str) -> None:
    if not syllabus.objectives:
        report.error("PRG-S18", where, "no course objectives")
    if not syllabus.outline:
        report.error("PRG-S18", where, "no topic outline")


def _authorship(syllabus: Syllabus, report: Report, where: str, *, creator: dict) -> None:
    if len(syllabus.changes) != 1 or syllabus.changes[0].action != "A":
        actions = [c.action for c in syllabus.changes]
        report.error(
            "PRG-S16",
            where,
            f"expected one 'A' change record, found {len(syllabus.changes)}"
            + (f" ({', '.join(actions)})" if actions else ""),
        )
    declared = syllabus.author("Creator")
    expected_name = creator.get("name")
    if expected_name and (declared is None or declared.name != expected_name):
        report.warn(
            "PRG-S17",
            where,
            f"creator is {declared.name if declared else 'absent'!r}, expected {expected_name!r}",
        )


def _rows(rows: list[dict[str, str]], report: Report, where: str) -> None:
    for index, row in enumerate(rows, start=2):
        delivery = row.get("Delivery Type", "")
        if delivery not in DELIVERY_TYPES:
            report.error("PRG-S03", where, f"row {index}: unknown delivery type {delivery!r}")
        if row.get("Training Format", "") != TRAINING_FORMAT:
            report.error(
                "PRG-S03",
                where,
                f"row {index}: training format is {row.get('Training Format', '')!r}, "
                f"expected {TRAINING_FORMAT!r}",
            )
        if as_number(row.get("Session", "")) is None:
            report.error("PRG-S04", where, f"row {index}: session is not a number")
        if as_number(row.get("Duration (mins)", "")) is None:
            report.error("PRG-S04", where, f"row {index}: duration is not a number")


def _minutes(syllabus: Syllabus, rows, report: Report, minutes_per_day: int) -> float:
    total = sum(as_number(row.get("Duration (mins)", "")) or 0 for row in rows)
    expected = syllabus.days * minutes_per_day
    if total != expected:
        report.error(
            "PRG-S05",
            syllabus.path.name,
            f"session plan totals {total:g} minutes but {syllabus.days} days at "
            f"{minutes_per_day} minutes is {expected}",
        )
    return total


def _sessions(
    rows, report: Report, where: str, minutes_per_day: int, max_per_chapter: float
) -> None:
    by_session: dict[float, float] = {}
    chapters_by_session: dict[float, set[tuple[str, str]]] = {}
    sessions_by_chapter: dict[tuple[str, str], set[float]] = {}

    for row in rows:
        session = as_number(row.get("Session", ""))
        if session is None:
            continue
        duration = as_number(row.get("Duration (mins)", "")) or 0
        chapter = (row.get("Unit", ""), row.get("Training Unit/Chapter", ""))
        by_session[session] = by_session.get(session, 0) + duration
        chapters_by_session.setdefault(session, set()).add(chapter)
        sessions_by_chapter.setdefault(chapter, set()).add(session)

    for session, minutes in sorted(by_session.items()):
        if minutes > minutes_per_day:
            report.error(
                "PRG-S06",
                where,
                f"session {session:g} runs {minutes:g} minutes; "
                f"a training day is {minutes_per_day}",
            )
    for session, chapters in sorted(chapters_by_session.items()):
        if len(chapters) != 1:
            names = ", ".join(sorted(name for _, name in chapters))
            report.error(
                "PRG-S07", where, f"session {session:g} spans {len(chapters)} chapters: {names}"
            )
    for chapter, sessions in sessions_by_chapter.items():
        if len(sessions) > max_per_chapter:
            report.warn(
                "PRG-S08",
                where,
                f"{chapter[1]!r} spans {len(sessions)} sessions; the limit is {max_per_chapter:g}",
            )


def _shares(syllabus: Syllabus, rows, total: float, report: Report, where: str) -> None:
    declared = syllabus.shares()
    for delivery_type in DELIVERY_TYPES:
        minutes = sum(
            as_number(row.get("Duration (mins)", "")) or 0
            for row in rows
            if row.get("Delivery Type", "") == delivery_type
        )
        expected = round(minutes / total * 100, 2)
        actual = declared.get(delivery_type)
        if actual is None:
            report.error("PRG-S09", where, f"Time Allocation has no row for {delivery_type!r}")
        elif abs(actual - expected) > SHARE_TOLERANCE:
            report.error(
                "PRG-S09",
                where,
                f"{delivery_type}: says {actual:.2f}% but the session plan gives "
                f"{expected:.2f}% ({minutes:g} of {total:g} minutes)",
            )


def _assessments(
    syllabus: Syllabus,
    rows,
    report: Report,
    where: str,
    *,
    pass_mark: int,
    item_patterns: dict[str, str] | None,
) -> None:
    items = list(syllabus.assessments)
    if not items:
        report.error("PRG-S10", where, "no assessment scheme")
        return

    if items[-1].item != PASS_CRITERIA:
        report.error(
            "PRG-S11", where, f"last row is {items[-1].item!r}, expected {PASS_CRITERIA!r}"
        )
    else:
        criteria = items[-1]
        if criteria.weight is not None:
            report.error("PRG-S11", where, f"{PASS_CRITERIA} carries a weight; it must be blank")
        if criteria.count != pass_mark:
            report.error(
                "PRG-S11",
                where,
                f"{PASS_CRITERIA} count is {criteria.count}, expected {pass_mark}",
            )

    scored = [item for item in items if item.item != PASS_CRITERIA]
    weights = [item.weight or 0 for item in scored]
    if scored and round(sum(weights), 6) != 100:
        report.error(
            "PRG-S10",
            where,
            f"weights sum to {sum(weights):g}%, not 100% "
            f"({', '.join(f'{i.item} {i.weight or 0:g}' for i in scored)})",
        )

    table = contracts_mod.registry(item_patterns)
    quiz_rows = []
    for item in scored:
        contract = table.get(item.item)
        if contract is None:
            report.warn(
                "PRG-S14",
                where,
                f"{item.item!r} has no row pattern, so its count of {item.count} is not checked",
            )
            continue
        counted = contracts_mod.count_occurrences(contract, rows)
        if item.count != counted:
            report.error(
                "PRG-S12",
                where,
                f"{item.item}: the scheme says {item.count} but the session plan delivers "
                f"{counted}",
            )
        if item.item == "Quiz":
            quiz_rows = [
                row
                for row in rows
                if contract.matches(row.get("Content", ""), row.get("Delivery Type", ""))
            ]

    if quiz_rows:
        units = {row.get("Unit", "") for row in quiz_rows}
        if len(units) < min(len(quiz_rows), 2):
            report.warn(
                "PRG-S13",
                where,
                f"{len(quiz_rows)} quizzes sit in {len(units)} chapter(s); spread them wider",
            )


def _objectives(syllabus: Syllabus, rows, report: Report, where: str) -> None:
    defined = {objective.code for objective in syllabus.objectives}
    if not defined:
        return
    for index, row in enumerate(rows, start=2):
        cited = OBJECTIVE_CODE.findall(row.get("Learning Objectives", ""))
        for code in cited:
            if code not in defined:
                report.warn(
                    "PRG-S19",
                    where,
                    f"row {index} cites {code}, which the syllabus does not define",
                )


__all__ = ["SHARE_TOLERANCE", "check"]

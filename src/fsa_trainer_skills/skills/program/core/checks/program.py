"""Programme-level rules: the curriculum document and its four CSVs."""

from __future__ import annotations

import math

from fsa_trainer_skills.errors import UsageError
from fsa_trainer_skills.findings import Report

from .. import schemas
from ..program import Program
from . import as_number, weekday_index


def check(
    program: Program,
    tables: dict,
    report: Report,
    *,
    first_weekday: str = "mon",
) -> None:
    _totals(program, report)
    minutes = _training_day(program, report)
    if minutes is not None:
        report.facts["minutes per training day"] = minutes

    master = tables.get("master")
    detailed = tables.get("detailed")
    topic_list = tables.get("topic_list")
    ost = tables.get("ost")

    weeks = _headers(master, schemas.MASTER_SCHEDULE, program, report)
    days = _headers(detailed, schemas.DETAILED_SCHEDULE, program, report)
    _headers(topic_list, schemas.TOPIC_LIST, program, report)
    _headers(ost, schemas.OST_MAPPING, program, report)

    if weeks is not None:
        report.facts["week columns"] = weeks
    if days is not None:
        report.facts["day columns"] = days
    if weeks is not None and days is not None:
        _weeks_match_days(weeks, days, report)

    for table, schema, column in (
        (master, schemas.MASTER_SCHEDULE, "Module"),
        (detailed, schemas.DETAILED_SCHEDULE, "Module"),
        (topic_list, schemas.TOPIC_LIST, "Topic Code"),
    ):
        _one_row_per_module(table, schema, column, program, report)

    _marks(master, weeks, report)
    _day_grid(detailed, days, program, report, first_weekday=first_weekday)
    _ost(ost, program, report)
    _topic_list(topic_list, program, report)


def _totals(program: Program, report: Report) -> None:
    hours = sum(module.hours for module in program.modules)
    days = sum(module.days for module in program.modules)
    where = program.path.name
    if not program.modules:
        report.error("PRG-P01", where, "no module table found under '### 1. The Modules'")
        return
    if hours != program.total_hours:
        report.error(
            "PRG-P01",
            where,
            f"module hours sum to {hours} but the TOTAL row says {program.total_hours}",
        )
    if days != program.total_days:
        report.error(
            "PRG-P01",
            where,
            f"module days sum to {days} but the TOTAL row says {program.total_days}",
        )
    report.facts["modules"] = len(program.modules)
    report.facts["total"] = f"{program.total_hours} hours over {program.total_days} days"


def _training_day(program: Program, report: Report) -> int | None:
    try:
        return program.minutes_per_day
    except UsageError as exc:
        report.error("PRG-P02", program.path.name, exc.message)
        return None


def _headers(table, schema, program: Program, report: Report) -> int | None:
    """Compare a table's header against its schema. Returns a derived tail size."""
    if table is None:
        return None
    count = 0
    if schema.index_prefix:
        try:
            count = schemas.derive_index_tail(table.headers, schema.index_prefix)
        except schemas.SchemaError as exc:
            report.error("PRG-P03", table.path.name, str(exc))
            return None
    expected = schemas.expected_headers(schema, count=count, modules=program.codes)
    if table.headers != expected:
        report.error(
            "PRG-P03",
            table.path.name,
            _header_diff(expected, table.headers),
        )
        return count if schema.index_prefix else None
    return count if schema.index_prefix else None


def _header_diff(expected: list[str], actual: list[str]) -> str:
    missing = [h for h in expected if h not in actual]
    extra = [h for h in actual if h not in expected]
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"missing {', '.join(missing[:6])}")
        if extra:
            parts.append(f"unexpected {', '.join(extra[:6])}")
        return "header does not match the schema: " + "; ".join(parts)
    return "header has the right columns in the wrong order"


def _one_row_per_module(table, schema, column: str, program: Program, report: Report) -> None:
    if table is None or column not in table.headers:
        return
    found = table.column(column)
    if found != list(program.codes):
        report.error(
            "PRG-P04",
            table.path.name,
            f"{column} column is {found or '[]'}; expected one row per module, in order: "
            f"{list(program.codes)}",
        )


def _marks(master, weeks: int | None, report: Report) -> None:
    if master is None or weeks is None:
        return
    columns = [f"W{n}" for n in range(1, weeks + 1)]
    for row in master.rows:
        marks = [name for name in columns if row.get(name, "").strip().lower() == "mark"]
        if len(marks) != 1:
            report.error(
                "PRG-P05",
                master.path.name,
                f"{row.get('Module', '?')}: expected exactly one assessment week, "
                f"found {len(marks)}" + (f" ({', '.join(marks)})" if marks else ""),
            )


def _day_grid(
    detailed, days: int | None, program: Program, report: Report, *, first_weekday: str
) -> None:
    if detailed is None or days is None:
        return
    columns = [f"D{n}" for n in range(1, days + 1)]
    offset = weekday_index(first_weekday)
    total = 0.0
    active: set[str] = set()
    for row in detailed.rows:
        declared = as_number(row.get("Drt (h)", ""))
        spent = 0.0
        for index, name in enumerate(columns, start=1):
            cell = row.get(name, "").strip()
            if not cell:
                continue
            active.add(name)
            value = as_number(cell)
            if value is None:
                report.error(
                    "PRG-P06",
                    detailed.path.name,
                    f"{row.get('Module', '?')} {name}: {cell!r} is not a number of hours",
                )
                continue
            spent += value
            if (offset + index - 1) % 7 >= 5:
                report.error(
                    "PRG-P09",
                    detailed.path.name,
                    f"{row.get('Module', '?')}: {name} falls on a weekend and must be blank",
                )
        if declared is None:
            report.error(
                "PRG-P06",
                detailed.path.name,
                f"{row.get('Module', '?')}: Drt (h) is not a number",
            )
            continue
        total += declared
        if spent != declared:
            report.error(
                "PRG-P06",
                detailed.path.name,
                f"{row.get('Module', '?')}: day cells total {spent:g}h "
                f"but Drt (h) says {declared:g}",
            )

    if total != program.total_hours:
        report.error(
            "PRG-P07",
            detailed.path.name,
            f"scheduled hours total {total:g} but the programme is {program.total_hours}",
        )
    if len(active) != program.total_days:
        report.error(
            "PRG-P08",
            detailed.path.name,
            f"{len(active)} days carry teaching but the programme runs {program.total_days}",
        )


def _weeks_match_days(weeks: int, days: int, report: Report) -> None:
    expected = math.ceil(days / 7)
    if weeks != expected:
        report.warn(
            "PRG-P10",
            "MasterSchedule",
            f"{days} day columns span {expected} weeks but there are {weeks} week columns",
        )


def _ost(ost, program: Program, report: Report) -> None:
    if ost is None:
        return
    codes = [code for code in program.codes if code in ost.headers]
    if not codes:
        return
    for row in ost.rows:
        if not any(row.get(code, "").strip() for code in codes):
            report.error(
                "PRG-P11",
                ost.path.name,
                f"{row.get('Code', '?')} is not mapped to any module",
            )


def _topic_list(topic_list, program: Program, report: Report) -> None:
    if topic_list is None or "Topic Name" not in topic_list.headers:
        return
    by_code = {module.code: module.name for module in program.modules}
    for row in topic_list.rows:
        code = row.get("Topic Code", "")
        expected = by_code.get(code)
        if expected is None:
            continue
        if row.get("Topic Name", "") != expected:
            report.error(
                "PRG-P12",
                topic_list.path.name,
                f"{code}: topic name is {row.get('Topic Name', '')!r} but the module table "
                f"says {expected!r}",
            )


__all__ = ["check"]

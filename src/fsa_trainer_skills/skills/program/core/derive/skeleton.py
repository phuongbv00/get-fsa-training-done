"""The four programme CSVs, as far as the module table determines them.

The headers and the one-row-per-module shape are a restatement of the module
table, so they are generated: a hand-typed `W1..W14` with a gap in it, or a row
order that drifts from the module table, breaks a join nothing reports until
export. What the tool cannot know — which week each module is assessed in, how
the hours fall across days, what each outcome standard says — is left blank for
a person to fill.
"""

from __future__ import annotations

import csv
import io
import math

from ..program import Program
from ..schedule import DELIVERY_TYPES  # noqa: F401  (documented vocabulary)
from ..schemas import (
    DETAILED_SCHEDULE,
    MASTER_SCHEDULE,
    OST_MAPPING,
    TOPIC_LIST,
    expected_headers,
)

#: A training week is five teaching days; the calendar columns run Monday to
#: Sunday and stop on the last teaching day, so the tail weekend is not written.
TEACHING_DAYS_PER_WEEK = 5
SESSION_LABEL = "Technical half-day"
DEFAULT_SEMESTER = "Semester 1"
DEFAULT_CONTENT_GROUP = "Common"


def week_count(training_days: int) -> int:
    return max(1, math.ceil(training_days / TEACHING_DAYS_PER_WEEK))


def day_column_count(training_days: int) -> int:
    """Calendar columns needed to hold `training_days` teaching days."""
    weeks = week_count(training_days)
    remainder = training_days - (weeks - 1) * TEACHING_DAYS_PER_WEEK
    return (weeks - 1) * 7 + remainder


def _dump(headers: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue()


def master(program: Program, *, weeks: int) -> str:
    headers = expected_headers(MASTER_SCHEDULE, count=weeks)
    rows = [
        [DEFAULT_SEMESTER, module.name, module.code] + [""] * weeks for module in program.modules
    ]
    return _dump(headers, rows)


def detailed(program: Program, *, days: int) -> str:
    headers = expected_headers(DETAILED_SCHEDULE, count=days)
    rows = [
        [DEFAULT_SEMESTER, module.name, module.code, str(module.hours), SESSION_LABEL] + [""] * days
        for module in program.modules
    ]
    return _dump(headers, rows)


def topic_list(program: Program) -> str:
    headers = expected_headers(TOPIC_LIST)
    rows = [
        [module.code, module.name, module.name, DEFAULT_CONTENT_GROUP] for module in program.modules
    ]
    return _dump(headers, rows)


def ost(program: Program, *, stub_rows: int = 0) -> str:
    headers = expected_headers(OST_MAPPING, modules=program.codes)
    rows = [[f"PO{n}"] + [""] * (len(headers) - 1) for n in range(1, stub_rows + 1)]
    return _dump(headers, rows)


BUILDERS = {
    "master": ("MasterSchedule.csv", lambda p, w, d, s: master(p, weeks=w)),
    "detailed": ("DetailedSchedule.csv", lambda p, w, d, s: detailed(p, days=d)),
    "topic-list": ("TopicList.csv", lambda p, w, d, s: topic_list(p)),
    "ost": ("OSTModuleMapping.csv", lambda p, w, d, s: ost(p, stub_rows=s)),
}


__all__ = [
    "BUILDERS",
    "SESSION_LABEL",
    "TEACHING_DAYS_PER_WEEK",
    "day_column_count",
    "detailed",
    "master",
    "ost",
    "topic_list",
    "week_count",
]

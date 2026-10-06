"""What each programme CSV must look like.

The reference pipeline hardcoded this programme's shape — seven modules, `W1`
through `W14`, `D1` through `D96`. None of that is a property of a programme in
general: the week and day counts follow from how long the programme runs, and
the module columns from its module table. So a schema here is a fixed prefix
plus a *derived* tail, and the verifier compares against what the sources say
rather than against a constant.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .schedule import SCHEDULE_HEADER

_INDEXED = re.compile(r"^([A-Za-z]+)(\d+)$")


@dataclass(frozen=True)
class TableSchema:
    name: str
    fixed: tuple[str, ...]
    #: Prefix of a `W1..Wn` / `D1..Dm` tail, or "" when the table has none.
    index_prefix: str = ""
    #: True when the columns after `fixed` are the programme's module codes.
    module_tail: bool = False


MASTER_SCHEDULE = TableSchema(
    name="MasterSchedule",
    fixed=("Semester", "Topics", "Module"),
    index_prefix="W",
)
DETAILED_SCHEDULE = TableSchema(
    name="DetailedSchedule",
    # `Session` here is the free string "Technical half-day"; in ScheduleDetail
    # the same column name holds a number. Same word, different type — so the
    # two schemas deliberately share no cell validator.
    fixed=("Semester", "Topic", "Module", "Drt (h)", "Session"),
    index_prefix="D",
)
TOPIC_LIST = TableSchema(
    name="TopicList",
    fixed=("Topic Code", "Topic Name", "Module", "Content Group"),
)
OST_MAPPING = TableSchema(
    name="OSTModuleMapping",
    fixed=(
        "Code",
        "Evaluation category",
        "Short Description",
        "Description",
        "Detail",
        "Evaluation Method",
        "Training Orientation",
    ),
    module_tail=True,
)
SCHEDULE_DETAIL = TableSchema(name="ScheduleDetail", fixed=SCHEDULE_HEADER)

ALL_SCHEMAS = (MASTER_SCHEDULE, DETAILED_SCHEDULE, TOPIC_LIST, OST_MAPPING, SCHEDULE_DETAIL)


class SchemaError(ValueError):
    pass


def derive_index_tail(headers: list[str], prefix: str) -> int:
    """How many `<prefix>N` columns follow, given they run 1..n without a gap.

    A gap is an error rather than something to work around: `W1,W3` means a
    column was deleted by hand, and silently treating it as two weeks would put
    every later assertion one column out.
    """
    tail = [h for h in headers if _INDEXED.match(h) and _INDEXED.match(h).group(1) == prefix]
    if not tail:
        raise SchemaError(f"no {prefix}N columns found")
    numbers = [int(_INDEXED.match(h).group(2)) for h in tail]
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        raise SchemaError(
            f"{prefix} columns must run {prefix}1..{prefix}{len(numbers)} in order; got "
            f"{', '.join(prefix + str(n) for n in numbers[:6])}"
            + ("..." if len(numbers) > 6 else "")
        )
    return len(numbers)


def expected_headers(
    schema: TableSchema, *, count: int = 0, modules: tuple[str, ...] = ()
) -> list[str]:
    """The full header row this schema requires for a given programme."""
    headers = list(schema.fixed)
    if schema.index_prefix:
        headers += [f"{schema.index_prefix}{n}" for n in range(1, count + 1)]
    if schema.module_tail:
        headers += list(modules)
    return headers


__all__ = [
    "ALL_SCHEMAS",
    "DETAILED_SCHEDULE",
    "MASTER_SCHEDULE",
    "OST_MAPPING",
    "SCHEDULE_DETAIL",
    "TOPIC_LIST",
    "SchemaError",
    "TableSchema",
    "derive_index_tail",
    "expected_headers",
]

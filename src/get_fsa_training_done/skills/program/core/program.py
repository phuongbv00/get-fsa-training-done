"""The programme curriculum document: `<PROGRAM>_TrainingProgramCurriculum.md`.

Everything the rest of the skill treats as a programme constant comes from here
— the module list, the hour and day totals, and from those two the length of a
training day. The reference pipeline hardcoded all of them; deriving them is
what makes the tooling work for a second programme.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from .mdtable import md_table_rows, section

MODULE_TABLE_HEADER = ("#", "Module Name", "Code", "Duration (hrs)", "Duration (days)")
TOTAL_LABEL = "TOTAL"


@dataclass(frozen=True)
class Module:
    number: int
    name: str
    code: str
    hours: int
    days: int
    description: str


@dataclass(frozen=True)
class Program:
    path: Path
    text: str
    title: str
    role: str
    modules: tuple[Module, ...]
    total_hours: int
    total_days: int

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(module.code for module in self.modules)

    @property
    def minutes_per_day(self) -> int:
        """Length of a training day, in minutes, from the totals.

        The reference pipeline carried 240 as a constant and separately asserted
        a 16800-minute grand total. Both are this one number in disguise:
        280 hours over 70 days is a 4-hour technical half-day. Deriving it means
        a programme that runs full days is not silently measured against
        someone else's timetable.
        """
        if self.total_days <= 0:
            raise UsageError("the TOTAL row has no day count, so a training day has no length")
        minutes = self.total_hours * 60 / self.total_days
        if minutes != int(minutes):
            raise UsageError(
                f"{self.total_hours} hours over {self.total_days} days is "
                f"{minutes:.2f} minutes per day, which is not a whole number"
            )
        return int(minutes)


def _int(value: str, *, what: str) -> int:
    try:
        return int(value.replace(",", "").strip())
    except ValueError:
        raise UsageError(f"{what} is not a number: {value!r}") from None


def parse(path: Path) -> Program:
    if not path.is_file():
        raise UsageError(f"curriculum not found: {path}")
    text = path.read_text(encoding="utf-8")

    title_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    role_match = re.search(r"^\*\*For Roles:\*\* (.+)$", text, re.MULTILINE)

    module_section = section(text, "### 1. The Modules", "### 2. Schedule Design")
    rows = md_table_rows(module_section)
    header_index = next(
        (
            index
            for index, row in enumerate(rows)
            if row[: len(MODULE_TABLE_HEADER)] == list(MODULE_TABLE_HEADER)
        ),
        -1,
    )
    modules: list[Module] = []
    total_hours = total_days = 0
    if header_index >= 0:
        for row in rows[header_index + 1 :]:
            if len(row) < 5:
                continue
            if row[1] == TOTAL_LABEL:
                total_hours = _int(row[3], what="TOTAL hours")
                total_days = _int(row[4], what="TOTAL days")
                continue
            if not row[0].isdigit():
                continue
            modules.append(
                Module(
                    number=int(row[0]),
                    name=row[1],
                    code=row[2],
                    hours=_int(row[3], what=f"{row[2]} hours"),
                    days=_int(row[4], what=f"{row[2]} days"),
                    description=row[5] if len(row) > 5 else "",
                )
            )

    return Program(
        path=path,
        text=text,
        title=title_match.group(1).strip() if title_match else "",
        role=role_match.group(1).strip() if role_match else "",
        modules=tuple(modules),
        total_hours=total_hours,
        total_days=total_days,
    )


__all__ = ["MODULE_TABLE_HEADER", "Module", "Program", "parse"]

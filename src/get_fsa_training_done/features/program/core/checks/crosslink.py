"""Rules that only make sense with the programme and every topic in hand.

Each half can be internally consistent while the two disagree — seven syllabi
that each add up, over a programme that promises a different number of days.
"""

from __future__ import annotations

from get_fsa_training_done.features.common.findings import Report

from .. import codes as codes_mod
from ..program import Program
from ..syllabus import Syllabus

AUDIENCE_FIELD = 5


def check(program: Program, syllabi: dict[str, Syllabus], report: Report) -> None:
    _pairs(program, syllabi, report)
    _days(program, syllabi, report)
    _codes(program, syllabi, report)


def _pairs(program: Program, syllabi: dict[str, Syllabus], report: Report) -> None:
    declared = set(program.codes)
    found = set(syllabi)
    where = program.path.name
    for code in sorted(declared - found):
        report.error("PRG-X01", where, f"{code} has no syllabus")
    for code in sorted(found - declared):
        report.error(
            "PRG-X01",
            where,
            f"{code} has a syllabus but is not in the module table",
        )


def _days(program: Program, syllabi: dict[str, Syllabus], report: Report) -> None:
    total = sum(syllabus.days for syllabus in syllabi.values())
    if syllabi and total != program.total_days:
        report.error(
            "PRG-X02",
            program.path.name,
            f"the syllabi declare {total} days between them but the programme runs "
            f"{program.total_days}",
        )
    for module in program.modules:
        syllabus = syllabi.get(module.code)
        if syllabus is not None and syllabus.days != module.days:
            report.error(
                "PRG-X03",
                syllabus.path.name,
                f"declares {syllabus.days} days but the module table says {module.days}",
            )


def _codes(program: Program, syllabi: dict[str, Syllabus], report: Report) -> None:
    prefixes = {}
    for code in program.codes:
        try:
            prefixes[code] = codes_mod.parse(code).prefix
        except codes_mod.CodeError as exc:
            report.warn("PRG-X04", program.path.name, str(exc))
    if prefixes:
        common = max(set(prefixes.values()), key=list(prefixes.values()).count)
        for code, prefix in prefixes.items():
            if prefix != common:
                report.warn(
                    "PRG-X04",
                    program.path.name,
                    f"{code} has prefix {prefix} but most topics use {common}",
                )

    for code, syllabus in sorted(syllabi.items()):
        level = codes_mod.level_for(code)
        audience = syllabus.fields.get(AUDIENCE_FIELD, "")
        # Only unbanded levels pin down an audience from a code alone; a banded
        # one has three different audiences and the code carries no band.
        if level is None or not audience:
            continue
        if level.audience.split()[0].lower() not in audience.lower():
            report.warn(
                "PRG-X05",
                syllabus.path.name,
                f"code claims {level.key} ({level.audience}) but the training audience "
                f"reads {audience!r}",
            )


__all__ = ["check"]

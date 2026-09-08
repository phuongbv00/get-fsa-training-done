"""Finding a programme's files, by the naming convention the corpus uses.

    <program-dir>/curriculum/<PROGRAM>_TrainingProgramCurriculum.md
                             <PROGRAM>_MasterSchedule.csv
                             <PROGRAM>_DetailedSchedule.csv
                             <PROGRAM>_TopicList.csv
                             <PROGRAM>_OSTModuleMapping.csv
                  curriculum/syllabi/<TOPIC>_Syllabus.md
                                     <TOPIC>_ScheduleDetail.csv

The programme code is read off the curriculum filename rather than configured,
so a directory holding one programme needs no arguments beyond its path. Every
file is optional at load time: a missing one becomes a finding, not a crash,
because reporting "this is absent" is more use than a traceback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from fsa_trainer_skills.errors import UsageError

from . import csvio
from . import program as program_mod
from . import syllabus as syllabus_mod
from .csvio import Table
from .program import Program
from .syllabus import Syllabus

CURRICULUM_SUFFIX = "_TrainingProgramCurriculum.md"
TABLE_SUFFIXES = {
    "master": "_MasterSchedule.csv",
    "detailed": "_DetailedSchedule.csv",
    "topic_list": "_TopicList.csv",
    "ost": "_OSTModuleMapping.csv",
}


@dataclass
class Bundle:
    program: Program
    curriculum_dir: Path
    syllabi_dir: Path
    tables: dict[str, Table] = field(default_factory=dict)
    syllabi: dict[str, Syllabus] = field(default_factory=dict)
    schedules: dict[str, Table] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)


def find_curriculum(curriculum_dir: Path) -> Path:
    matches = sorted(curriculum_dir.glob(f"*{CURRICULUM_SUFFIX}"))
    if not matches:
        raise UsageError(
            f"no *{CURRICULUM_SUFFIX} found in {curriculum_dir}",
            hint="pass --curriculum to name it explicitly",
        )
    if len(matches) > 1:
        raise UsageError(
            f"{len(matches)} curriculum documents in {curriculum_dir}: "
            + ", ".join(p.name for p in matches),
            hint="pass --curriculum to choose one",
        )
    return matches[0]


def load(
    program_dir: Path,
    *,
    curriculum: Path | None = None,
    syllabi_dir: Path | None = None,
    topic: str | None = None,
) -> Bundle:
    program_dir = program_dir.expanduser().resolve()
    curriculum_dir = program_dir / "curriculum"
    if not curriculum_dir.is_dir():
        # A directory holding the curriculum files directly is just as valid.
        curriculum_dir = program_dir
    curriculum_path = curriculum or find_curriculum(curriculum_dir)
    curriculum_dir = curriculum_path.parent
    program = program_mod.parse(curriculum_path)

    code = curriculum_path.name[: -len(CURRICULUM_SUFFIX)]
    bundle = Bundle(
        program=program,
        curriculum_dir=curriculum_dir,
        syllabi_dir=syllabi_dir or (curriculum_dir / "syllabi"),
    )

    for key, suffix in TABLE_SUFFIXES.items():
        path = curriculum_dir / f"{code}{suffix}"
        if path.is_file():
            bundle.tables[key] = csvio.read_table(path)
        else:
            bundle.missing.append(path.name)

    if bundle.syllabi_dir.is_dir():
        for path in sorted(bundle.syllabi_dir.glob("*_Syllabus.md")):
            parsed = syllabus_mod.parse(path)
            name = path.stem[: -len("_Syllabus")]
            if topic and name != topic:
                continue
            bundle.syllabi[name] = parsed
            schedule = bundle.syllabi_dir / f"{name}_ScheduleDetail.csv"
            if schedule.is_file():
                bundle.schedules[name] = csvio.read_table(schedule)
            else:
                bundle.missing.append(schedule.name)

    return bundle


__all__ = ["Bundle", "CURRICULUM_SUFFIX", "TABLE_SUFFIXES", "find_curriculum", "load"]

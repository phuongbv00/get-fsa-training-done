"""Fixtures specific to the `assess` skill's own tests."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parents[2] / "fixtures" / "assess"


@pytest.fixture
def quiz_master_rows() -> list[list[str]]:
    text = (FIXTURES / "question_set" / "quiz_master.csv").read_text(encoding="utf-8")
    return [row for row in csv.reader(text.splitlines())]


@pytest.fixture
def long_form_pair(tmp_path) -> tuple[Path, Path]:
    """The canonical brief and rubric, copied somewhere writable."""
    brief = tmp_path / "sbf_practice_exam_02.md"
    rubric = tmp_path / "sbf_practice_exam_02_rubric.md"
    shutil.copyfile(FIXTURES / "long_form" / brief.name, brief)
    shutil.copyfile(FIXTURES / "long_form" / rubric.name, rubric)
    return brief, rubric


@pytest.fixture
def capstone_trio(tmp_path) -> tuple[Path, Path, Path]:
    """The canonical capstone brief, spec, and rubric, copied somewhere writable."""
    names = (
        "mkp_capstone_project_01.md",
        "mkp_capstone_project_01_spec.md",
        "mkp_capstone_project_01_rubric.md",
    )
    paths = []
    for name in names:
        target = tmp_path / name
        shutil.copyfile(FIXTURES / "capstone" / name, target)
        paths.append(target)
    return tuple(paths)


@pytest.fixture
def roster_csv(tmp_path) -> Path:
    path = tmp_path / "std_list.csv"
    # utf-8-sig: real rosters come out of Excel with a BOM.
    path.write_text(
        "No,ID,Name,Status\n"
        "1,PhuongBV3,Bui Van Phuong,active\n"
        "2,LinhTT127,Tran Thi Linh,active\n"
        "3,HieuLX14,Le Xuan Hieu,dropped\n"
        "4,AnhPQ54,Pham Quynh Anh,inactive\n",
        encoding="utf-8-sig",
    )
    return path

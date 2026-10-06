"""Fixtures for the programme skill's tests.

The good corpus lives in `tests/fixtures/program/mini` and is small enough to
read: two modules, five training days. Every failing case is produced by
copying it and making one targeted edit, rather than by keeping dozens of
near-identical broken trees that rot the moment the schema moves.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from get_fsa_training_done.cli import main

#: The clean programme ships *in the payload*, so the example the model reads
#: and the fixture the tests trust are the same bytes. A consistency gate keeps
#: it verifying clean; `tests/fixtures/program/` holds only broken variants.
from get_fsa_training_done.features.program import SKILL

MINI = SKILL.payload_dir / "references" / "examples" / "mini"


@pytest.fixture(autouse=True)
def no_venv(monkeypatch):
    """Worker commands re-exec into the managed venv; keep them in-process here.

    Without this every call builds a venv under the test's temporary home and
    pip-installs into it, which turns a millisecond check into a network round
    trip and hangs the suite.
    """
    monkeypatch.setenv("GET_FSA_TRAINING_DONE_NO_VENV", "1")


@pytest.fixture
def mini(tmp_path):
    """A writable copy of the clean programme."""
    target = tmp_path / "mini"
    shutil.copytree(MINI, target)
    return target


@pytest.fixture
def verify(capsys):
    """Run `program verify` over a directory and return its JSON report."""

    def run(program_dir: Path, *extra: str) -> dict:
        capsys.readouterr()
        main(["program", "verify", "--program-dir", str(program_dir), "--json", *extra])
        return json.loads(capsys.readouterr().out)

    return run


@pytest.fixture
def fired(verify):
    """The set of rule ids a directory triggers."""

    def run(program_dir: Path, *extra: str) -> set[str]:
        return {f["rule"] for f in verify(program_dir, *extra)["findings"]}

    return run


@pytest.fixture
def edit():
    """Replace text in a file under the programme copy, asserting it matched."""

    def apply(root: Path, relative: str, old: str, new: str, count: int = 1) -> Path:
        path = root / relative
        text = path.read_text(encoding="utf-8")
        assert text.count(old) >= 1, f"{relative} does not contain {old!r}"
        path.write_text(text.replace(old, new, count), encoding="utf-8")
        return path

    return apply


@pytest.fixture
def synthetic_xlsx(tmp_path):
    """A minimal but realistic workbook, written to disk.

    Built here rather than committed, and deliberately carrying every feature
    the real vendor form has that a naive round-trip loses: a shared-string
    cell, a formula with a cached value, a calc chain, a defined name quoting
    a sheet by name, and an opaque binary part. CI must never need the
    proprietary template.
    """
    import zipfile

    from .synthetic import SYNTHETIC_PARTS

    path = tmp_path / "Template_Synthetic.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        for name, body in SYNTHETIC_PARTS.items():
            archive.writestr(name, body if isinstance(body, bytes) else body.encode("utf-8"))
    return path


@pytest.fixture
def vendor_form(tmp_path):
    """A workbook with the same sheets, anchors and quirks as the FPT form.

    Including the two the exporter has to cope with: the summary block lists
    delivery types in a different order from the syllabus table, and the data
    band ships under sample merges that would swallow written rows.
    """
    import zipfile

    from .synthetic import vendor_form_parts

    path = tmp_path / "Template_Vendor.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        for name, body in vendor_form_parts().items():
            archive.writestr(name, body if isinstance(body, bytes) else body.encode("utf-8"))
    return path

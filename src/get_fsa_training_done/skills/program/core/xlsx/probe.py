"""Checking a template is the shape the layout map assumes, before writing.

The writers address cells by fixed reference — the assessment block starts at
row 28 because that is where the vendor form puts it. That is only defensible
if something verifies the assumption first: handed a revised form, a writer
addressing row 28 does not fail, it writes the right value into the wrong cell
and produces a workbook that looks plausible and is wrong.

So a layout map declares what it expects to find, and this reports precisely
which cell disagreed.
"""

from __future__ import annotations

from dataclasses import dataclass

from get_fsa_training_done.errors import FsaTrainerSkillsError

from .package import XlsxPackage

#: The template ships defined names that are already `#REF!` — two of the real
#: form's three are. Only *cell values* are scanned for error literals.
ERROR_LITERALS = ("#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#N/A")


@dataclass(frozen=True)
class Expect:
    sheet: str
    ref: str
    value: str
    #: Any of these is acceptable, for a cell whose wording varies by revision.
    alternatives: tuple[str, ...] = ()

    def accepts(self, found: str | None) -> bool:
        candidates = {self.value, *self.alternatives}
        return (found or "").strip() in {c.strip() for c in candidates}


def probe(package: XlsxPackage, sheets: list[str], expectations: list[Expect]) -> list[str]:
    """Problems with this template, as readable lines."""
    problems: list[str] = []
    present = package.sheet_names()
    for name in sheets:
        if name not in present:
            problems.append(f"missing sheet {name!r}; found {', '.join(present)}")

    cached: dict[str, object] = {}
    for expectation in expectations:
        if expectation.sheet not in present:
            continue
        sheet = cached.get(expectation.sheet)
        if sheet is None:
            sheet = package.sheet(expectation.sheet)
            cached[expectation.sheet] = sheet
        found = sheet.value_of(expectation.ref)
        if not expectation.accepts(found):
            problems.append(
                f"{expectation.sheet}!{expectation.ref}: expected {expectation.value!r}, "
                f"found {found!r}"
            )
    return problems


def require(package: XlsxPackage, sheets: list[str], expectations: list[Expect]) -> None:
    problems = probe(package, sheets, expectations)
    if problems:
        raise FsaTrainerSkillsError(
            f"{package.path.name} is not the template this exporter was written for",
            hint="; ".join(problems[:5]),
        )


def error_cells(package: XlsxPackage, sheet_name: str) -> list[str]:
    """Cells whose value is a spreadsheet error literal."""
    sheet = package.sheet(sheet_name)
    found = []
    for ref in sheet.refs_present():
        value = (sheet.value_of(ref) or "").strip()
        if value in ERROR_LITERALS:
            found.append(f"{sheet_name}!{ref} = {value}")
    return found


__all__ = ["ERROR_LITERALS", "Expect", "error_cells", "probe", "require"]

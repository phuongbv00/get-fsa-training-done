"""What every FAMS import shares, whichever of its two forms it takes.

FAMS takes marks in two forms, each from a template downloaded per class:

- **the theory mark template** (`fams_theory`) — one row per trainee per test, a final
  mark only. Quizzes and the theory exam.
- **the practice mark template** (`fams_practice`) — one row per trainee: a mark per task
  over the task weights, with topic, assessment, marker and date above. The
  assignments and the practice exam.

Both follow the rules FAMS enforces on import, and they live here once:

- **The template decides who is in the class.** A trainee with marks it does
  not list is left out (FAMS rejects anyone not enrolled) and reported; a
  template trainee with no marks is written as 0 and reported. Without a
  template, every active roster trainee.
- **The account is the roster's**: the FPT account id, or the roster's
  `Account` for a trainee FAMS knows by another (a CPL trainee's personal
  email) — never the email a template ships with. A template row the roster
  cannot place keeps its own account and is reported.
- **No blank mark**: FAMS refuses one, so whatever is missing is written as 0.

Each form's writer is `zipfile` and hand-written XML for the generated
workbook, so an export needs no spreadsheet library.
"""

from __future__ import annotations

import zipfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

from .roster import Roster, Trainee, name_key


@dataclass
class Report:
    """What an export did that the user must hear before importing."""

    rows: int = 0
    #: Trainees with marks the template does not list, so left out.
    left_out: list[str] = field(default_factory=list)
    #: Class trainees with no marks at all, written as 0.
    zeroed: list[str] = field(default_factory=list)
    #: Template rows the roster cannot place: their account is the template's.
    unmatched: list[str] = field(default_factory=list)
    #: (test, trainee id) pairs written as 0 because that one test was missed.
    missed: list[tuple[str, str]] = field(default_factory=list)
    #: The header values written above the table, by label.
    info: dict[str, str] = field(default_factory=dict)
    #: Anything else worth a line, already worded.
    notes: list[str] = field(default_factory=list)


class Marks[E]:
    """A source's rows, found by the trainee a class row names, or by name."""

    def __init__(
        self, entries: Iterable[E], std_id: Callable[[E], str], name: Callable[[E], str]
    ) -> None:
        self.entries = list(entries)
        self._std_id = std_id
        self._by_id = {std_id(e).strip().lower(): e for e in self.entries}
        self._by_name = {name_key(name(e)): e for e in self.entries if name(e).strip()}
        self._used: set[int] = set()

    def find(self, trainee: Trainee | None, name: str) -> E | None:
        entry = self._by_id.get(trainee.std_id.lower()) if trainee else None
        if entry is None and name.strip():
            entry = self._by_name.get(name_key(name))
        if entry is not None:
            self._used.add(id(entry))
        return entry

    def place(self, roster: Roster, account: str, name: str) -> tuple[Trainee | None, E | None]:
        """The trainee a class row names and their marks. A row the roster
        cannot place by account or name is still theirs when the marks match
        it by name: their id then finds them on the roster."""
        trainee = roster.find(account, name)
        entry = self.find(trainee, name)
        if trainee is None and entry is not None:
            trainee = roster.get(self._std_id(entry))
        return trainee, entry

    def unused(self) -> list[str]:
        """Ids of the rows no class row asked for: the left-out trainees."""
        return [self._std_id(e) for e in self.entries if id(e) not in self._used]


# --- the generated workbook --------------------------------------------------------

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"


def write_workbook(out: Path, sheet_name: str, sheet_xml: str, styles_xml: str) -> None:
    """A one-sheet `.xlsx` from its sheet and stylesheet parts."""
    parts = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" '
            'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{_PKG}">'
            f'<Relationship Id="rId1" Type="{_REL}/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        ),
        "xl/workbook.xml": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<workbook xmlns="{NS}" xmlns:r="{_REL}"><sheets>'
            f'<sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{_PKG}">'
            f'<Relationship Id="rId1" Type="{_REL}/worksheet" Target="worksheets/sheet1.xml"/>'
            f'<Relationship Id="rId2" Type="{_REL}/styles" Target="styles.xml"/>'
            "</Relationships>"
        ),
        "xl/styles.xml": styles_xml,
        "xl/worksheets/sheet1.xml": sheet_xml,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, body in parts.items():
            archive.writestr(name, body)

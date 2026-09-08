"""Reading the programme CSVs.

UTF-8 with a BOM tolerated, RFC 4179 quoting via the standard library, and every
cell a string — blanks are `""`, never `None`, because "no hours scheduled that
day" and "zero hours" have to be distinguishable and the CSVs express the first
as an empty cell.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from fsa_trainer_skills.errors import UsageError


@dataclass(frozen=True)
class Table:
    path: Path
    headers: list[str]
    rows: list[dict[str, str]]

    def column(self, name: str) -> list[str]:
        return [row.get(name, "") for row in self.rows]


def read_table(path: Path) -> Table:
    if not path.is_file():
        raise UsageError(f"CSV not found: {path}")
    # utf-8-sig: exported-from-Excel files routinely carry a BOM, and a BOM on
    # the first header turns "Semester" into something that matches nothing.
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            headers = [cell.strip() for cell in next(reader)]
        except StopIteration:
            raise UsageError(f"{path.name} is empty") from None
        rows = [
            {
                header: (row[index].strip() if index < len(row) else "")
                for index, header in enumerate(headers)
            }
            for row in reader
            if any(cell.strip() for cell in row)
        ]
    return Table(path=path, headers=headers, rows=rows)


__all__ = ["Table", "read_table"]

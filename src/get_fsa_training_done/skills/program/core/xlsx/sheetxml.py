"""Editing one worksheet's XML in place.

Every rule here exists because of something the real vendor template does:

* Cells carry a style index (`s="144"`). Replacing a value must keep it, or the
  cell loses the formatting the form supplies — this writer never creates a
  style, it populates a formatted template.
* Strings are written **inline**. Appending to `sharedStrings.xml` would mean
  keeping its `count`/`uniqueCount` correct for no benefit; cells we do not
  touch keep using it, and that part is copied through untouched.
* Numbers must be written as numbers. The template's summary block is a `SUMIF`
  over the duration column, and it silently returns 0 when the durations are
  text.
* A formula cell caches its last value (`<f>…</f><v>0.389…</v>`). Writing a
  literal over one without removing the `<f>`, or leaving a stale `<v>` beside a
  formula, shows the old number until Excel recalculates.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from . import refs

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("", MAIN)


def q(tag: str) -> str:
    return f"{{{MAIN}}}{tag}"


class Sheet:
    """One `xl/worksheets/sheetN.xml`."""

    def __init__(self, data: bytes) -> None:
        self.root = ET.fromstring(data)

    # -- structure ---------------------------------------------------------

    @property
    def sheet_data(self) -> ET.Element:
        node = self.root.find(q("sheetData"))
        if node is None:
            node = ET.SubElement(self.root, q("sheetData"))
        return node

    def _row(self, number: int) -> ET.Element:
        rows = self.sheet_data.findall(q("row"))
        for row in rows:
            if int(row.get("r", 0)) == number:
                return row
        element = ET.Element(q("row"), {"r": str(number)})
        position = len(rows)
        for index, row in enumerate(rows):
            if int(row.get("r", 0)) > number:
                position = index
                break
        self.sheet_data.insert(position, element)
        return element

    def cell(self, ref: str, *, create: bool = True) -> ET.Element | None:
        column, row_number = refs.split(ref)
        row = self._row(row_number) if create else None
        if row is None:
            for candidate in self.sheet_data.findall(q("row")):
                if int(candidate.get("r", 0)) == row_number:
                    row = candidate
                    break
            if row is None:
                return None
        cells = row.findall(q("c"))
        for element in cells:
            if refs.split(element.get("r", "A1"))[0] == column:
                return element
        if not create:
            return None
        element = ET.Element(q("c"), {"r": refs.cell(column, row_number)})
        position = len(cells)
        for index, existing in enumerate(cells):
            if refs.split(existing.get("r", "A1"))[0] > column:
                position = index
                break
        row.insert(position, element)
        return element

    # -- values ------------------------------------------------------------

    @staticmethod
    def _empty(element: ET.Element) -> None:
        """Strip value and type, keeping the style the template supplies."""
        for tag in ("f", "v", "is"):
            for child in element.findall(q(tag)):
                element.remove(child)
        element.attrib.pop("t", None)

    def set_text(self, ref: str, value: str) -> None:
        element = self.cell(ref)
        self._empty(element)
        element.set("t", "inlineStr")
        wrapper = ET.SubElement(element, q("is"))
        text = ET.SubElement(wrapper, q("t"))
        text.text = value
        if value != value.strip():
            text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    def set_number(self, ref: str, value: float) -> None:
        element = self.cell(ref)
        self._empty(element)
        node = ET.SubElement(element, q("v"))
        node.text = str(int(value)) if float(value).is_integer() else repr(float(value))

    def set_formula(self, ref: str, formula: str) -> None:
        element = self.cell(ref)
        self._empty(element)
        node = ET.SubElement(element, q("f"))
        node.text = formula.lstrip("=")

    def clear(self, ref: str) -> None:
        element = self.cell(ref, create=False)
        if element is not None:
            self._empty(element)

    def clear_range(self, range_ref: str) -> None:
        for ref in refs.expand(range_ref):
            self.clear(ref)

    def style_of(self, ref: str) -> str | None:
        element = self.cell(ref, create=False)
        return element.get("s") if element is not None else None

    def set_style(self, ref: str, style: str | None) -> None:
        if style is None:
            return
        self.cell(ref).set("s", style)

    def value_of(self, ref: str) -> str | None:
        """The literal text in a cell — inline string, or a cached value."""
        element = self.cell(ref, create=False)
        if element is None:
            return None
        inline = element.find(f"{q('is')}/{q('t')}")
        if inline is not None:
            return inline.text or ""
        value = element.find(q("v"))
        return value.text if value is not None else None

    # -- sheet-level -------------------------------------------------------

    def refs_present(self) -> list[str]:
        return [
            element.get("r")
            for row in self.sheet_data.findall(q("row"))
            for element in row.findall(q("c"))
            if element.get("r")
        ]

    def update_dimension(self) -> None:
        """Excel treats `dimension` as a hint; LibreOffice trusts it."""
        node = self.root.find(q("dimension"))
        if node is None:
            node = ET.Element(q("dimension"))
            self.root.insert(0, node)
        node.set("ref", refs.bounds(self.refs_present()))

    def set_merges(self, ranges: list[str]) -> None:
        for existing in self.root.findall(q("mergeCells")):
            self.root.remove(existing)
        if not ranges:
            return
        node = ET.Element(q("mergeCells"), {"count": str(len(ranges))})
        for value in ranges:
            ET.SubElement(node, q("mergeCell"), {"ref": value})
        # Schema order: mergeCells sits after sheetData.
        children = list(self.root)
        index = children.index(self.sheet_data) + 1
        self.root.insert(index, node)

    def merges(self) -> list[str]:
        return [
            element.get("ref", "")
            for node in self.root.findall(q("mergeCells"))
            for element in node.findall(q("mergeCell"))
        ]

    def to_bytes(self) -> bytes:
        return ET.tostring(self.root, encoding="UTF-8", xml_declaration=True)


__all__ = ["MAIN", "Sheet", "q"]

"""The workbook as a zip of parts, most of which we never touch.

Opening reads every part once and keeps the archive's entry order. Saving walks
that same order, substituting the parts we rewrote and writing the rest back
under a `ZipInfo` copied field for field.

One honest caveat: `zipfile` exposes no public raw-stream copy, so untouched
parts are decompressed and recompressed with their original method. The part
*contents* are byte-identical and the entry order and metadata are preserved;
the compressed container bytes may differ. Tests compare per-part content, never
the archive as a whole.
"""

from __future__ import annotations

import posixpath
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from fsa_trainer_skills.errors import UsageError

from .sheetxml import Sheet

CONTENT_TYPES = "[Content_Types].xml"
WORKBOOK = "xl/workbook.xml"
WORKBOOK_RELS = "xl/_rels/workbook.xml.rels"
CALC_CHAIN = "xl/calcChain.xml"

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"

ET.register_namespace("", MAIN)

#: Excel's own limits on a sheet name.
INVALID_SHEET_CHARS = set(r"[]:*?/\\")
MAX_SHEET_NAME = 31


class XlsxPackage:
    def __init__(self, path: Path) -> None:
        if path.suffix.lower() != ".xlsx":
            raise UsageError(
                f"{path.name} is not a .xlsx file",
                hint=(
                    "this reads the Open XML package directly, which the older .xls "
                    "format is not; open it in a spreadsheet application and save a "
                    ".xlsx copy, then pass that"
                ),
            )
        if not path.is_file():
            raise UsageError(f"template not found: {path}")
        self.path = path
        self.order: list[str] = []
        self.infos: dict[str, zipfile.ZipInfo] = {}
        self.parts: dict[str, bytes] = {}
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                self.order.append(info.filename)
                self.infos[info.filename] = info
                self.parts[info.filename] = archive.read(info.filename)

    # -- parts -------------------------------------------------------------

    def replace(self, name: str, data: bytes) -> None:
        if name not in self.parts:
            raise KeyError(f"{name} is not in {self.path.name}")
        self.parts[name] = data

    def delete(self, name: str) -> None:
        """Drop a part, its relationship, and its content-type override."""
        if name not in self.parts:
            return
        del self.parts[name]
        self.order.remove(name)
        self._drop_override(name)
        self._drop_relationship(name)

    def _drop_override(self, name: str) -> None:
        root = ET.fromstring(self.parts[CONTENT_TYPES])
        target = "/" + name
        for override in root.findall(f"{{{TYPES}}}Override"):
            if override.get("PartName") == target:
                root.remove(override)
        self.parts[CONTENT_TYPES] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)

    def _drop_relationship(self, name: str) -> None:
        for rels_name in list(self.parts):
            if not rels_name.endswith(".rels"):
                continue
            base = posixpath.dirname(posixpath.dirname(rels_name))
            root = ET.fromstring(self.parts[rels_name])
            changed = False
            for relationship in list(root.findall(f"{{{PACKAGE_RELS}}}Relationship")):
                target = relationship.get("Target", "")
                resolved = posixpath.normpath(posixpath.join(base, target.lstrip("/")))
                if resolved == name:
                    root.remove(relationship)
                    changed = True
            if changed:
                self.parts[rels_name] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)

    def shared_strings(self) -> list[str]:
        """The shared-string table, read only.

        Template labels are stored here, and the layout map matches on them —
        the summary block's delivery types, the delivery-principle rows. This
        writer never *adds* to the table; everything it writes is inline.
        """
        part = "xl/sharedStrings.xml"
        if part not in self.parts:
            return []
        root = ET.fromstring(self.parts[part])
        values = []
        for item in root.findall(f"{{{MAIN}}}si"):
            values.append("".join(node.text or "" for node in item.iter(f"{{{MAIN}}}t")))
        return values

    # -- sheets ------------------------------------------------------------

    def sheet_names(self) -> list[str]:
        root = ET.fromstring(self.parts[WORKBOOK])
        return [
            element.get("name", "") for element in root.findall(f"{{{MAIN}}}sheets/{{{MAIN}}}sheet")
        ]

    def sheet_part(self, name: str) -> str:
        """Resolve a sheet name to its part, via the workbook and its rels."""
        root = ET.fromstring(self.parts[WORKBOOK])
        rel_id = None
        for element in root.findall(f"{{{MAIN}}}sheets/{{{MAIN}}}sheet"):
            if element.get("name") == name:
                rel_id = element.get(f"{{{RELS}}}id")
                break
        if rel_id is None:
            raise UsageError(
                f"{self.path.name} has no sheet named {name!r}",
                hint="sheets present: " + ", ".join(self.sheet_names()),
            )
        rels = ET.fromstring(self.parts[WORKBOOK_RELS])
        for relationship in rels.findall(f"{{{PACKAGE_RELS}}}Relationship"):
            if relationship.get("Id") == rel_id:
                target = relationship.get("Target", "")
                return posixpath.normpath(posixpath.join("xl", target.lstrip("/")))
        raise UsageError(f"{self.path.name}: sheet {name!r} has no part")

    def sheet(self, name: str) -> Sheet:
        return Sheet(self.parts[self.sheet_part(name)])

    def write_sheet(self, name: str, sheet: Sheet) -> None:
        sheet.update_dimension()
        self.replace(self.sheet_part(name), sheet.to_bytes())

    def rename_sheet(self, old: str, new: str) -> None:
        """Rename a sheet, and every reference that quotes its name.

        A defined name or a cross-sheet formula still quoting the old name
        resolves to `#REF!` — the real template's `_xlnm._FilterDatabase` does
        exactly that, so this is not hypothetical.
        """
        if new == old:
            return
        if len(new) > MAX_SHEET_NAME:
            raise UsageError(f"sheet name {new!r} is {len(new)} characters; the limit is 31")
        if set(new) & INVALID_SHEET_CHARS:
            raise UsageError(f"sheet name {new!r} contains a character Excel forbids")
        if new in self.sheet_names():
            raise UsageError(f"{self.path.name} already has a sheet named {new!r}")

        root = ET.fromstring(self.parts[WORKBOOK])
        found = False
        for element in root.findall(f"{{{MAIN}}}sheets/{{{MAIN}}}sheet"):
            if element.get("name") == old:
                element.set("name", new)
                found = True
        if not found:
            raise UsageError(f"{self.path.name} has no sheet named {old!r}")
        for defined in root.findall(f"{{{MAIN}}}definedNames/{{{MAIN}}}definedName"):
            defined.text = _requote(defined.text or "", old, new)
        self.parts[WORKBOOK] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)

        for part in list(self.parts):
            if part.startswith("xl/worksheets/sheet") and part.endswith(".xml"):
                text = self.parts[part].decode("utf-8")
                updated = _requote(text, old, new)
                if updated != text:
                    self.parts[part] = updated.encode("utf-8")

    def drop_sheet(self, name: str) -> None:
        """Remove a sheet, renumbering the defined names that index into the list.

        `definedName/@localSheetId` is a position in `<sheets>`, so removing one
        shifts every later index.
        """
        if name not in self.sheet_names():
            return
        part = self.sheet_part(name)
        root = ET.fromstring(self.parts[WORKBOOK])
        sheets = root.find(f"{{{MAIN}}}sheets")
        removed_index = None
        for index, element in enumerate(list(sheets)):
            if element.get("name") == name:
                removed_index = index
                sheets.remove(element)
                break
        if removed_index is None:  # pragma: no cover - guarded above
            return
        defined_names = root.find(f"{{{MAIN}}}definedNames")
        if defined_names is not None:
            for defined in list(defined_names):
                raw = defined.get("localSheetId")
                if raw is None:
                    continue
                index = int(raw)
                if index == removed_index:
                    defined_names.remove(defined)
                elif index > removed_index:
                    defined.set("localSheetId", str(index - 1))
            if len(defined_names) == 0:
                root.remove(defined_names)
        self.parts[WORKBOOK] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)

        rels_part = f"xl/worksheets/_rels/{posixpath.basename(part)}.rels"
        self.delete(part)
        if rels_part in self.parts:
            self.delete(rels_part)

    # -- recalculation -----------------------------------------------------

    def force_full_recalc(self) -> None:
        """Ask the reader to recompute on open.

        The template's summary block and its cross-sheet percentages are
        formulas with cached values. Changing the data they read without this
        shows the template's numbers until someone edits a cell.
        """
        root = ET.fromstring(self.parts[WORKBOOK])
        calc = root.find(f"{{{MAIN}}}calcPr")
        if calc is None:
            calc = ET.SubElement(root, f"{{{MAIN}}}calcPr")
        calc.set("fullCalcOnLoad", "1")
        self.parts[WORKBOOK] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)

    def drop_calc_chain(self) -> None:
        """A chain naming cells whose formulas changed makes Excel report the
        file as unreadable. Deleting it makes Excel rebuild silently."""
        self.delete(CALC_CHAIN)

    # -- output ------------------------------------------------------------

    def save(self, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w") as archive:
            for name in self.order:
                if name not in self.parts:
                    continue
                source = self.infos[name]
                info = zipfile.ZipInfo(filename=name, date_time=source.date_time)
                info.compress_type = source.compress_type
                info.external_attr = source.external_attr
                info.internal_attr = source.internal_attr
                info.create_system = source.create_system
                info.comment = source.comment
                archive.writestr(info, self.parts[name])


def _requote(text: str, old: str, new: str) -> str:
    """Swap a sheet name wherever a formula or defined name quotes it."""
    return (
        text.replace(f"'{old}'!", f"'{new}'!")
        .replace(f"&apos;{old}&apos;!", f"&apos;{new}&apos;!")
        .replace(f"{old}!", f"{new}!")
    )


__all__ = ["CALC_CHAIN", "CONTENT_TYPES", "WORKBOOK", "WORKBOOK_RELS", "XlsxPackage"]

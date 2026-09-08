# ruff: noqa: E501
"""The parts of a synthetic workbook, kept verbatim.

Open XML content types and relationship types are long fixed URIs. Wrapping
them would change the bytes, so line length is waived for this file alone
rather than for the tests that use it.

Built here rather than committed, and deliberately carrying every feature the
real vendor form has that a naive round-trip loses: a shared-string cell, a
formula with a cached value, a calc chain, a defined name quoting a sheet by
name, and an opaque binary part. CI must never need the proprietary template.
"""

from __future__ import annotations

SYNTHETIC_PARTS = {
    "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="bin" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.printerSettings"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
<Override PartName="/xl/calcChain.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.calcChain+xml"/>
</Types>""",
    "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
    "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>
<sheet name="Cover" sheetId="1" r:id="rId1"/>
<sheet name="&lt;Topic Code&gt;_Syllabus" sheetId="2" r:id="rId2"/>
</sheets>
<definedNames>
<definedName name="_xlnm._FilterDatabase" localSheetId="1" hidden="1">'&lt;Topic Code&gt;_Syllabus'!$A$1:$C$2</definedName>
<definedName name="Stale" localSheetId="0" hidden="1">#REF!</definedName>
</definedNames>
<calcPr calcId="191028"/>
</workbook>""",
    "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/calcChain" Target="calcChain.xml"/>
</Relationships>""",
    "xl/sharedStrings.xml": """<?xml version="1.0" encoding="UTF-8"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="2" uniqueCount="2">
<si><t>Topic Name</t></si><si><t>Quiz</t></si>
</sst>""",
    "xl/worksheets/sheet1.xml": """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<dimension ref="A1:A1"/><sheetData><row r="1"><c r="A1" s="3"><v>1</v></c></row></sheetData>
</worksheet>""",
    "xl/worksheets/sheet2.xml": """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<dimension ref="A1:C5"/>
<sheetData>
<row r="1"><c r="A1" s="7" t="s"><v>0</v></c></row>
<row r="2"><c r="A2" s="11"><v>1</v></c><c r="C2" s="12" t="s"><v>1</v></c></row>
<row r="3"><c r="B3" s="9"><f>SUM(A2:A2)</f><v>1</v></c></row>
<row r="5"><c r="A5" s="4"/></row>
</sheetData>
<mergeCells count="1"><mergeCell ref="A1:B1"/></mergeCells>
</worksheet>""",
    "xl/calcChain.xml": """<?xml version="1.0" encoding="UTF-8"?>
<calcChain xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><c r="B3" i="2"/></calcChain>""",
    "xl/printerSettings/printerSettings1.bin": b"\x00opaque-binary-part\x00",
}


def _sheet_xml(cells: dict, merges: tuple = ()) -> str:
    """A worksheet from {ref: (style, kind, value)} where kind is s|n|f."""
    from xml.sax.saxutils import escape

    rows: dict = {}
    for ref, (style, kind, value) in cells.items():
        number = int("".join(c for c in ref if c.isdigit()))
        rows.setdefault(number, []).append((ref, style, kind, value))
    body = []
    for number in sorted(rows):
        parts = [f'<row r="{number}">']
        for ref, style, kind, value in sorted(
            rows[number], key=lambda item: len("".join(c for c in item[0] if c.isalpha()))
        ):
            if kind == "s":
                parts.append(
                    f'<c r="{ref}" s="{style}" t="inlineStr">'
                    f"<is><t>{escape(str(value))}</t></is></c>"
                )
            elif kind == "n":
                parts.append(f'<c r="{ref}" s="{style}"><v>{value}</v></c>')
            else:
                parts.append(f'<c r="{ref}" s="{style}"><f>{escape(str(value))}</f><v>0</v></c>')
        parts.append("</row>")
        body.append("".join(parts))
    merge_xml = ""
    if merges:
        inner = "".join(f'<mergeCell ref="{ref}"/>' for ref in merges)
        merge_xml = f'<mergeCells count="{len(merges)}">{inner}</mergeCells>'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<dimension ref="A1:I80"/><sheetData>'
        + "".join(body)
        + "</sheetData>"
        + merge_xml
        + "</worksheet>"
    )


DELIVERY_ORDER = (
    "Concept/Lecture",
    "Assignment/Lab",
    "Guides/Review",
    "Test/Quiz",
    "Exam",
    "Seminar/Workshop",
    "Class Meeting",
)
#: The syllabus table lists them in a different order from the summary block —
#: exactly as the real form does, which is why the exporter matches on label.
TABLE_ORDER = (
    "Concept/Lecture",
    "Assignment/Lab",
    "Guides/Review",
    "Seminar/Workshop",
    "Class Meeting",
    "Test/Quiz",
    "Exam",
)


def vendor_form_parts() -> dict:
    """A workbook shaped like the FPT syllabus form, with the same anchors."""
    syllabus = {}
    for row, number in (
        (2, 1),
        (3, 2),
        (4, 3),
        (5, 4),
        (6, 5),
        (7, 6),
        (17, 7),
        (18, 8),
        (25, 9),
        (28, 10),
        (33, 11),
    ):
        syllabus[f"A{row}"] = ("70", "n", number)
    for offset, name in enumerate(TABLE_ORDER):
        syllabus[f"C{18 + offset}"] = ("71", "s", name)
        # Two cells the vendor leaves as a literal zero rather than a formula.
        syllabus[f"D{18 + offset}"] = ("72", "n", 0)
    for row, label in ((25, "Text book"), (26, "References"), (27, "Technical requirements")):
        syllabus[f"C{row}"] = ("73", "s", label)
    for offset, label in enumerate(
        ("Quiz", "Assignments", "Final Theory Test", "Final Practice Test", "Pass Criteria")
    ):
        syllabus[f"C{28 + offset}"] = ("74", "s", label)
    for offset, label in enumerate(
        ("Trainees", "Trainer", "Training", "Re-Test", "Marking", "Waiver Criteria", "Others")
    ):
        syllabus[f"C{33 + offset}"] = ("75", "s", label)
    syllabus["C8"] = ("76", "s", "Name")
    syllabus["D8"] = ("76", "s", "Code")
    syllabus["E8"] = ("76", "s", "Description")

    schedule = {"A2": ("80", "s", "Training Unit/Chapter")}
    for offset, header in enumerate(
        (
            "Session",
            "Content",
            "Learning Objectives",
            "Delivery Type",
            "Duration (mins)",
            "Training Format",
            "Training Materials / Logistics & General Notes",
        )
    ):
        schedule[f"{chr(ord('C') + offset)}2"] = ("80", "s", header)
    # Sample rows the exporter must clear, under merges it must rebuild.
    for row in range(3, 10):
        schedule[f"A{row}"] = ("81", "n", 1)
        schedule[f"B{row}"] = ("81", "s", "Sample chapter")
        schedule[f"D{row}"] = ("81", "s", "Sample content")
    for offset, name in enumerate(DELIVERY_ORDER):
        schedule[f"F{70 + offset}"] = ("82", "s", name)
        schedule[f"G{70 + offset}"] = ("83", "f", f"SUMIF(F$3:F$68,F{70 + offset},G$3:G$68)")
        schedule[f"H{70 + offset}"] = ("84", "f", f"G{70 + offset}/$G$77")
    schedule["F77"] = ("82", "s", "Total")
    schedule["G77"] = ("83", "f", "SUM(G70:G76)")

    author = {"A1": ("90", "s", "AUTHORSHIP")}
    for offset, role in enumerate(("Creator", "Reviewer", "Approver")):
        author[f"B{3 + offset}"] = ("91", "s", role)
    author["A6"] = ("90", "s", "RECORD OF CHANGES")

    parts = dict(SYNTHETIC_PARTS)
    parts["xl/workbook.xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        '<sheet name="Cover" sheetId="1" r:id="rId1"/>'
        '<sheet name="&lt;Topic Code&gt;_Syllabus" sheetId="2" r:id="rId2"/>'
        '<sheet name="&lt;Topics Code&gt;_ScheduleDetail" sheetId="3" r:id="rId5"/>'
        '<sheet name="Author and Rec of Changes" sheetId="4" r:id="rId6"/>'
        '<sheet name="DV-IDENTITY-0" sheetId="5" state="veryHidden" r:id="rId7"/>'
        "</sheets><definedNames>"
        '<definedName name="_xlnm._FilterDatabase" localSheetId="2" hidden="1">'
        "'&lt;Topics Code&gt;_ScheduleDetail'!$A$1:$I$2</definedName>"
        '</definedNames><calcPr calcId="191028"/></workbook>'
    )
    parts["xl/_rels/workbook.xml.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/'
            f'2006/relationships/worksheet" Target="worksheets/{part}"/>'
            for rid, part in (
                ("rId1", "sheet1.xml"),
                ("rId2", "sheet2.xml"),
                ("rId5", "sheet3.xml"),
                ("rId6", "sheet4.xml"),
                ("rId7", "sheet5.xml"),
            )
        )
        + '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/sharedStrings" Target="sharedStrings.xml"/>'
        '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/calcChain" Target="calcChain.xml"/>'
        "</Relationships>"
    )
    parts["xl/worksheets/sheet2.xml"] = _sheet_xml(syllabus, merges=("A7:A16", "C16:F16"))
    parts["xl/worksheets/sheet3.xml"] = _sheet_xml(
        schedule, merges=("A2:B2", "A3:A9", "B3:B9", "C3:C4")
    )
    parts["xl/worksheets/sheet4.xml"] = _sheet_xml(author)
    parts["xl/worksheets/sheet5.xml"] = _sheet_xml({"A1": ("1", "s", "identity")})
    types = parts["[Content_Types].xml"].replace(
        '<Override PartName="/xl/sharedStrings.xml"',
        "".join(
            f'<Override PartName="/xl/worksheets/sheet{n}.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for n in (3, 4, 5)
        )
        + '<Override PartName="/xl/sharedStrings.xml"',
    )
    parts["[Content_Types].xml"] = types
    return parts

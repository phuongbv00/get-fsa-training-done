"""What a template placeholder's first paragraph looks like, inheritance resolved.

PowerPoint resolves a placeholder's text style from the layout's list style, then
the master's title or body style, and its colours through the master's colour
map and theme. `test_layouts.py` resolves the same chain on the shipped
`fsa_base.pptx`, so `core/layouts.py` cannot drift from the template it claims
to reproduce.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
TITLE_TYPES = {"title", "ctrTitle"}


@dataclass
class Style:
    size: int | None = None  # points
    bold: bool | None = None
    italic: bool | None = None
    font: str | None = None
    colour: str | None = None  # RRGGBB
    align: str | None = None  # l | ctr | r
    anchor: str | None = None  # t | ctr | b


def _merge(into: Style, lvl, body_pr) -> None:
    """Fill the fields `into` does not have yet from a `lvl1pPr` and a `bodyPr`."""
    if lvl is not None:
        if into.align is None and lvl.get("algn"):
            into.align = lvl.get("algn")
        rpr = lvl.find("a:defRPr", NS)
        if rpr is not None:
            if into.size is None and rpr.get("sz"):
                into.size = int(rpr.get("sz")) // 100
            if into.bold is None and rpr.get("b") is not None:
                into.bold = rpr.get("b") == "1"
            if into.italic is None and rpr.get("i") is not None:
                into.italic = rpr.get("i") == "1"
            latin = rpr.find("a:latin", NS)
            if into.font is None and latin is not None:
                into.font = latin.get("typeface")
            fill = rpr.find("a:solidFill", NS)
            if into.colour is None and fill is not None:
                into.colour = fill
    if body_pr is not None and into.anchor is None and body_pr.get("anchor"):
        into.anchor = body_pr.get("anchor")


def _scheme(prs) -> dict[str, str]:
    master = prs.slide_masters[0]
    theme_part = next(
        rel.target_part for rel in master.part.rels.values() if rel.reltype.endswith("/theme")
    )
    xml = theme_part.blob.decode()
    colours = {}
    for name in ("dk1", "lt1", "dk2", "lt2", *(f"accent{n}" for n in range(1, 7))):
        block = re.search(rf"<a:{name}>(.*?)</a:{name}>", xml, re.S).group(1)
        value = re.search(r'(?:val|lastClr)="([0-9A-Fa-f]{6})"', block)
        colours[name] = value.group(1).upper() if value else "000000"
    if "windowText" in xml and "<a:dk1><a:sysClr" in xml:
        colours["dk1"] = "000000"
    if "<a:lt1><a:sysClr" in xml:
        colours["lt1"] = "FFFFFF"
    clr_map = master._element.find("p:clrMap", NS)
    for alias in ("bg1", "tx1", "bg2", "tx2"):
        colours[alias] = colours[clr_map.get(alias)]
    return colours


def _colour(fill, scheme: dict[str, str]) -> str | None:
    if fill is None:
        return None
    srgb = fill.find("a:srgbClr", NS)
    if srgb is not None:
        return srgb.get("val").upper()
    named = fill.find("a:schemeClr", NS)
    if named is None:
        return None
    value = scheme.get(named.get("val"), "000000")
    lum = named.find("a:lumMod", NS)
    if lum is not None:
        factor = int(lum.get("val")) / 100000
        value = "".join(f"{round(int(value[i : i + 2], 16) * factor):02X}" for i in (0, 2, 4))
    return value


def resolve(prs, layout, idx: int) -> Style:
    shape = next(sh for sh in layout.placeholders if sh.placeholder_format.idx == idx)
    kind = shape._element.find(".//p:nvPr/p:ph", NS).get("type", "body")
    style = Style()
    tx = shape._element.find("p:txBody", NS)
    if tx is not None:
        _merge(style, tx.find("a:lstStyle/a:lvl1pPr", NS), tx.find("a:bodyPr", NS))

    master = prs.slide_masters[0]
    wanted = "title" if kind in TITLE_TYPES else "body"
    for sp in master.placeholders:
        ph = sp._element.find(".//p:nvPr/p:ph", NS)
        if ph.get("type", "body") == wanted:
            body = sp._element.find("p:txBody", NS)
            _merge(style, body.find("a:lstStyle/a:lvl1pPr", NS), body.find("a:bodyPr", NS))
            break
    styles = master._element.find("p:txStyles", NS)
    tag = "p:titleStyle" if wanted == "title" else "p:bodyStyle"
    _merge(style, styles.find(f"{tag}/a:lvl1pPr", NS), None)

    style.colour = _colour(style.colour, _scheme(prs))
    style.anchor = style.anchor or "t"
    style.align = style.align or "l"
    style.bold = bool(style.bold)
    style.italic = bool(style.italic)
    return style

"""Reading a slide deck into slides, slots and speaker notes.

Shared by `verify`, which checks the deck against the template, and by both
exporters, which place each slot into the template's placeholder for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import layouts as L
from .dom import Document, Element


@dataclass
class Slide:
    #: 1-based, as a trainer would count them.
    number: int
    element: Element
    layout_name: str
    layout: L.Layout | None
    slots: dict[str, Element] = field(default_factory=dict)
    notes: Element | None = None
    #: `check` for a retrieval question; empty otherwise.
    role: str = ""
    #: Elements outside any slot and outside the notes: content with no
    #: placeholder to go to.
    stray: list[Element] = field(default_factory=list)
    #: `data-slot` names the layout does not have.
    unknown_slots: list[str] = field(default_factory=list)

    @property
    def line(self) -> int:
        return self.element.line

    @property
    def role_kind(self) -> str:
        return self.layout.role if self.layout else ""

    def title(self) -> str:
        slot = self.slots.get("title")
        if slot is not None and slot.text():
            return slot.text()
        if self.layout is not None:
            spec = self.layout.slot("title")
            if spec is not None:
                return spec.default
        return ""

    def where(self) -> str:
        return f"slide {self.number} ({self.layout_name or '?'})"


def read(document: Document) -> list[Slide]:
    slides = []
    for number, element in enumerate(document.body.find_all("section", class_="slide"), 1):
        name = element.get("data-layout")
        slide = Slide(
            number=number,
            element=element,
            layout_name=name,
            layout=L.BY_NAME.get(name),
            role=element.get("data-role"),
        )
        for child in element.elements:
            if child.tag == "aside" and "notes" in child.classes:
                slide.notes = child
                continue
            slot_name = child.get("data-slot")
            if not slot_name:
                slide.stray.append(child)
                continue
            if slide.layout is not None and slide.layout.slot(slot_name) is None:
                slide.unknown_slots.append(slot_name)
            slide.slots[slot_name] = child
        slides.append(slide)
    return slides


def sections(slides: list[Slide]) -> list[tuple[Slide, list[Slide]]]:
    """Each section cover with the slides it opens, up to the summary."""
    found: list[tuple[Slide, list[Slide]]] = []
    for slide in slides:
        if slide.role_kind == L.SECTION:
            found.append((slide, []))
        elif slide.role_kind in (L.SUMMARY, L.CLOSING):
            break
        elif found:
            found[-1][1].append(slide)
    return found


def section_titles(slides: list[Slide]) -> list[str]:
    """What the table of contents lists: the section covers' titles, in order."""
    return [cover.title() for cover, _ in sections(slides)]


def objective_items(slide: Slide) -> list[Element]:
    body = slide.slots.get("body")
    return body.find_all("li") if body is not None else []


__all__ = ["Slide", "objective_items", "read", "section_titles", "sections"]

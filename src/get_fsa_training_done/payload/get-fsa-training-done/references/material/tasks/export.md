# Task — Export material to PowerPoint and PDF

The HTML is the source; the `.pptx` and `.pdf` are derived from it, rebuilt
whenever it changes and never edited by hand.

## Inputs

| Input | Notes |
|---|---|
| the documents | a deck, or a note, lab or handbook, already passing `verify` |

## Produces

Beside each source: `NN_Topic_Name.deck.pptx` and `.deck.pdf` for a deck (16:9,
on the FSA template), and an A4 `.pdf` for the lecture note, a lab or the
handbook. A lecture note is handed out as its HTML and that PDF only.

## Steps

1. Check what an export cannot carry first:

   ```bash
   FSA material verify "<materials_dir>" --export
   ```

   `MAT-X01` is a diagram with no image: PowerPoint and the PDF writer cannot
   run Mermaid, so put a PNG of it in the same `<figure>` (`<img src="…png"
   alt="…">`), or accept that the export shows its source. `MAT-X03` is an image
   an export will not embed: an SVG (export it to PNG) or a file outside the
   module's folder (move it in).
2. Export:

   ```bash
   FSA material export pptx "<materials_dir>/NN_Topic_Name.deck.html"
   FSA material export pdf  "<materials_dir>/NN_Topic_Name.deck.html"
   FSA material export pdf  "<materials_dir>/<subject>_lecture_note.html"
   ```

   Export refuses a document with errors; fix the HTML rather than passing
   `--force`.
3. Read the warnings. `MAT-X02` from the deck's PDF is a slot whose text does not
   fit even shrunk: split the slide, or move the detail to the speaker notes and
   the lecture note.
4. Answers folded into `<details>` on a check slide go into that slide's notes in
   the `.pptx`, never onto the slide.

## Done when

Every file is written, with no `MAT-X02`, and every `MAT-X01` is fixed or named
as accepted.

## Hands off to

Nothing. Re-export after every change to the HTML.

# `material` — writing, checking and exporting teaching material

Write the teaching material a session plan calls for, check that what the plan
promises exists, and export what is handed out. The agent writes the content;
the CLI checks the shape everything downstream depends on, counts the parts of
good teaching that can be counted, and derives what must not be maintained by
hand.

| | |
| --- | --- |
| Namespace | `material` |
| Part of the skill | `get-fsa-training-done` |
| Worker commands | `gftd material <verb>` |
| Payload | [`references/material/`](../payload/get-fsa-training-done/references/material) |

## Artifacts

Material is **HTML on the FSA theme**, one file per artifact. The HTML is the
single source of truth; the `.pptx` and `.pdf` are exported from it. In order of
how much a trainee learns from them:

| Artifact | File | Exports to |
| --- | --- | --- |
| Slide deck | `NN_Topic_Name.deck.html` | `.pptx` on the FSA template, 16:9 `.pdf` |
| Module handbook | `00_Study_Guide_Handbook.html` — index `00` is reserved | A4 `.pdf` |
| Lecture note | `NN_Topic_Name.html` — shares its deck's index | A4 `.pdf` |
| Lab guide | `<subject>_lab_NN.html` | A4 `.pdf` |
| Group worksheet | `<subject>_lab_NN_worksheet.html` — a blank form beside a group lab | |
| Module appendix | `99_Appendix.html` — its syllabus map is derived | |

A deck follows the template: cover, table of contents, Lesson Objectives, one
section cover per section, Lesson Summary, Thank you. Each slide names one of the
template's layouts (`data-layout`) and fills its placeholders (`data-slot`);
speaker notes are `<aside class="notes">`. Open it in a browser to present it
(arrow keys, N for notes, O for the overview), or export it.

A note, lab or handbook is a sequence of `<section data-part="…">`: a note has
objectives, why it matters, one concept per idea with a try-it and its answer, a
worked example, common problems, a summary and a knowledge check with answers.

A lab guide is the **guided middle**: shorter than an assignment,
step-numbered, and checkable by the learner without a marker. If it carries
marks and a rubric it is an assignment, and it belongs to the assessment
feature.

**Outline first.** The skill writes no document until its outline — slides
with their layouts, a note's parts and try-its, a lab's steps against its
minutes — has been shown and explicitly approved
([`propose_outline.md`](../payload/get-fsa-training-done/references/material/tasks/propose_outline.md)).
A consistency test keeps that gate the first step of every writing task.

## The theme

`theme/` holds what every page links to, copied into a module by `init`:

- `fsa.css` — colours, type and every component; hand-written.
- `layouts.css` — each slide layout's background and slot boxes; **generated**
  from `core/layouts.py`.
- `deck.js` — the deck viewer; `doc.js` — the document helper. No dependencies;
  Mermaid is fetched only for a diagram with no image beside it.
- `img/` — the template's backgrounds, and the header band for documents.
- `fsa_base.pptx` — the template's master and layouts with no slides, which
  `export pptx` writes into. Not copied by `init`.

`fsa_base.pptx` and `img/` are built from the FSA Training Materials template by
[`scripts/material/build_theme.py`](../../../../scripts/material/build_theme.py),
run by hand once per template version. It drops the sample slides and the brand
slides, recompresses the images, and removes the embedded Calibri and Segoe UI,
which are Microsoft's to license. Committing the theme is a deliberate exception
to "a customer's template is never committed".

## The seam with the other two features

A session row in a programme's plan names the file that serves it. That column
is the contract:

```csv
1,Semantic HTML,1,"Lab: build an accessible two-breakpoint page",FEF-K1,Assignment/Lab,90,Blended,fef_lab_01.html
1,Relational Modelling,1,Quiz 1 — modelling scenarios (MCQ),DBF-K1,Test/Quiz,30,Blended,dbf_quiz_01.csv
```

The program feature writes the row. This feature produces `fef_lab_01.html`; the
assessment feature produces `dbf_quiz_01.csv`. `coverage` reports what is
missing on this side and counts the rest as *owned by another feature* rather than
as a gap — reporting a missing quiz here would send someone to write the wrong
thing.

## Worker commands

### `init` — put the theme beside the material

```bash
gftd material init --dir "training_program/10. RE/Lectures"
```

Creates or refreshes `<dir>/_theme/`, so the folder opens correctly from a file
share or a zip with nothing installed.

### `verify` — is the material well formed, and does it teach?

```bash
gftd material verify "training_program/10. RE/Lectures"
gftd material verify 01_Relational_Modelling.deck.html --minutes-per-slide 2-5
gftd material verify "training_program/10. RE/Lectures" --export
```

Prefer a folder: the index rules only mean anything across a whole module.

- `MAT-D*` — one document: its kind and metas, the theme and no inline styling,
  well-formed HTML, the parts in order, code languages, links and ids, diagrams,
  and the learning rules (answers to every question, every objective tested, a
  try-it after each concept, prose before code, what to expect after each lab
  step).
- `MAT-S*` — a deck against the template: its order, its layouts and slots, the
  objectives the session claims stated and summarised, speaker notes, a check
  slide per section, slot limits, and a slide count that fits the minutes.
- `MAT-X*` — what an export cannot carry, with `--export`.

Every finding names its rule, and
[`references/material/structure.md`](../payload/get-fsa-training-done/references/material/structure.md)
is **generated** from `core/grammar.py` and `core/rules.py`, as
[`layouts.md`](../payload/get-fsa-training-done/references/material/layouts.md)
is from `core/layouts.py` — prose describing a rule the checker does not enforce
would calibrate the model to a constraint nothing holds it to.

### `coverage` — does what the plan asks for exist?

```bash
gftd material coverage \
  --schedule HN_FR_JSKS_FEF_ScheduleDetail.csv \
  --dir "training_program/5. FEF/Lectures" \
  --syllabus HN_FR_JSKS_FEF_Syllabus.md
```

Both directions: a file the plan names that does not exist is an error, a file
present that no session uses is a warning. With `--syllabus` it also checks the
objective codes against the syllabus, and that a material mentions the
objectives its session claims. Only `.html` counts: a plan still naming a
lecture or lab as `.md` is reported missing, with the name it should have.

It reads the plan **by column name, tolerating any superset**, and deliberately
does not enforce that CSV's schema — that is `program verify`'s job.

### `derive appendix` — the syllabus map

```bash
gftd material derive appendix \
  --syllabus TOPIC_Syllabus.md --dir ./Lectures --appendix 99_Appendix.html --write
```

Matches each topic-outline item to the note whose title or part headings best
cover it, and rewrites the appendix's `syllabus-map` part as a checklist of
links. It is a match on wording, so the result is meant to be read. `--check` is
the drift gate; `--write` is idempotent.

### `export` — the files handed out

```bash
gftd material export pptx 01_Relational_Modelling.deck.html
gftd material export pdf  01_Relational_Modelling.deck.html
gftd material export pdf  01_Relational_Modelling.html
```

Verifies first and refuses a document with errors. `pptx` adds each slide from
the template's own layout and fills its placeholders; a check slide's answer
goes to the notes. `pdf` draws a deck with reportlab, shrinking a slot's text to
fit and reporting `MAT-X02` past a readable floor; a long-form document is
rendered by `xhtml2pdf` with the embedded fonts `assessment render` uses.

## Language

A document is written in the language its `<html lang>` declares — `en` by
default, `vi` for a module written in Vietnamese. Everything the skill writes on
the author's behalf follows it: slide defaults, the theme's labels, the viewer's
hints, a PDF's session line, the appendix heading. Those words live once, in
`core/i18n.py`; `gen_layouts.py` generates the stylesheet's labels from it.
A translation of an English original is a **separate file** whose stem ends
`_vn` and declares `vi`. `verify` warns about Vietnamese in a file that does not
declare it (`MAT-D16`).

## Prerequisites

`python-pptx` and `xhtml2pdf` (which brings reportlab), in the managed venv.

## Layout

```
features/material/
├── commands/            # init, verify, coverage, derive, export
├── core/
│   ├── grammar.py       # the kinds and their parts — source for structure.md
│   ├── layouts.py       # the template's slide layouts — source for layouts.md/.css
│   ├── rules.py         # the rulebook
│   ├── dom.py           # the HTML element tree
│   ├── deck.py          # slides, slots and notes
│   ├── checks.py        # MAT-D*/MAT-S* rule bodies
│   ├── rich.py          # a slot's content as blocks, for the exporters
│   ├── export_pptx.py   # into the template
│   ├── export_pdf.py    # slides with reportlab, documents with xhtml2pdf
│   ├── coverage.py      # MAT-C*, the cross-feature half
│   └── appendix.py      # the derived syllabus map
└── theme/               # fsa.css, layouts.css (GENERATED), deck.js, doc.js, img/, fsa_base.pptx

payload/get-fsa-training-done/references/material/
├── overview.md
├── structure.md, layouts.md   # GENERATED
├── conventions.md
├── templates/           # deck, lecture note, lab, handbook, appendix (HTML)
├── examples/{mini,plan}/
├── tasks/
└── workflows/
```

## Development

```bash
python scripts/material/gen_structure_md.py   # after editing grammar.py or rules.py
python scripts/material/gen_layouts.py        # after editing layouts.py
python scripts/material/build_theme.py ~/path/Template_FSA_Training\ Materials_v1.0.pptx
```

CI runs the two generators with `--check`; `build_theme.py` needs the template,
which is not in the repository, so only a person runs it.

The clean example module lives in the payload
([`references/material/examples/mini/`](../payload/get-fsa-training-done/references/material/examples/mini)),
with the session plan that asks for it in `examples/plan/`. Consistency gates assert it verifies clean
*and* covers its plan exactly, and that every shipped template would itself pass
the checker. Failing cases are copies of the example with one targeted edit.

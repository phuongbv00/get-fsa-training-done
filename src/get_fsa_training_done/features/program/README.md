# `program` — designing a training programme

Design a training programme, check that every artifact reconciles against the
others, and export the vendor workbook. The agent authors the content; the CLI
does the deterministic work — deriving the tables that summarise other files,
reconciling the numbers, and editing the workbook.

| | |
| --- | --- |
| Namespace | `program` |
| Part of the skill | `get-fsa-training-done` |
| Worker commands | `get-fsa-training-done program <verb>` |
| Payload | [`references/program/`](../payload/get-fsa-training-done/references/program) |

## What it owns

| Level | Artifacts |
| --- | --- |
| Programme | the curriculum document, master and detailed schedules, the topic list, the outcome-standard mapping |
| Topic | one syllabus and one session plan per module |
| Delivered | the FPT vendor workbook, one per topic |

It declares assessment **slots** — that a quiz exists, what it weighs, and the
filename that will serve it — and never the instrument. A session's
`Training Materials` cell is the manifest binding the three features: `program`
says a slot exists, `assessment` writes the quiz, and `material` writes the
lecture note or lab guide.

## Nothing is a constant

The pipeline this replaces hardcoded one programme: seven modules, 280 hours,
70 days, a 240-minute training day, a 16800-minute total, `W1..W14`, `D1..D96`.
None of that is a property of a programme in general, so all of it is derived:

| Figure | Comes from |
| --- | --- |
| module count, codes, order | the module table |
| total hours and days | its TOTAL row, which the rows must sum to |
| the length of a training day | total hours ÷ total days |
| week and day column counts | the CSV headers, which must run from 1 with no gaps |
| a topic's day count | its session plan's minutes ÷ a training day |

If a figure cannot be derived, the sources disagree — which is a finding, not a
number to pick.

## Worker commands

### `verify` — does it reconcile?

```bash
get-fsa-training-done program verify --program-dir ./docs/HN_FR_JSKS_JAVA_WEB
get-fsa-training-done program verify --program-dir . --topic HN_FR_JSKS_DBF --json
```

36 rules across three scopes — `PRG-P*` the programme files, `PRG-S*` one topic,
`PRG-X*` the links between them. Every finding carries its rule id, and
[`references/program/rules.md`](../payload/get-fsa-training-done/references/program/rules.md) is
**generated** from `core/rules.py` so the prose cannot promise a constraint the
checker does not enforce.

Errors mean the artifacts contradict each other; warnings mean something looks
wrong but may be deliberate — a capstone really does group a chapter by sprint.
`--strict` promotes warnings.

Policy that is genuinely a judgement call is a flag, not an assumption:
`--first-weekday`, `--pass-mark`, `--max-sessions-per-chapter`, `--creator`,
`--item-pattern`.

### `derive` — what must not be typed twice

```bash
get-fsa-training-done program derive allocation --schedule plan.csv --syllabus s.md --write
get-fsa-training-done program derive skeleton --curriculum c.md --out-dir .
```

`allocation` recomputes a syllabus's §8 Time Allocation from its session plan;
`skeleton` writes the four programme CSVs' headers and one row per module from
the module table. Both exist for the same reason `assessment emit` does: a table
that summarises another file drifts from it the moment it is written by hand.

`--check` is the drift gate; `--write` is idempotent.

### `export` — fill the vendor workbook

```bash
get-fsa-training-done program export syllabus \
  --template Template_Import_Syllabus.xlsx --syllabus s.md -o DBF_Syllabus.xlsx
```

Verifies first and refuses sources that do not reconcile. The template is the
customer's property: it is never shipped here, and `--template` takes `.xlsx`
only.

## How export treats the workbook

It **edits** a copy of the template rather than rebuilding it. The sheets being
populated are rewritten and every other part of the package is copied through
untouched.

That is not fastidiousness. Measured on the real form: an openpyxl round trip
drops the classification label, both custom-property blobs and all four
printer-settings parts, and the Node pipeline this replaces emitted 17 of the
template's 35 parts. Editing in place emits 32 — losing only the calc chain,
which readers rebuild, and the form's dead identity sheet.

Consequences worth knowing:

- **No new styles.** `core/xlsx/` never touches `styles.xml`; it reuses the
  style each cell already has, so it populates a formatted template and cannot
  invent formatting.
- **A fixed band.** The session plan writes into a fixed row range with the
  summary block immediately below it. A longer plan is refused rather than
  allowed to overwrite the formulas the syllabus reads.
- **Percentages stay formulas.** §8 points at the schedule sheet's summary, so
  the workbook recomputes them. The form maps those by *label*, not position —
  its summary lists the delivery types in a different order from the syllabus
  table — so the exporter matches on label too, which also repairs two cells the
  vendor left as a literal `0`.

## Prerequisites

None. Everything runs in the managed virtualenv, and the workbook editing is
standard library only (`zipfile` plus `xml.etree`).

## Layout

```
features/program/
├── commands/            # verify, derive, export
└── core/
    ├── program.py       # the curriculum document
    ├── syllabus.py      # a topic syllabus
    ├── schemas.py       # CSV shapes, with derived column tails
    ├── rules.py         # the rulebook — source for rules.md
    ├── contracts.py     # matching assessment items to the sessions delivering them
    ├── checks/          # rule bodies: program, topic, crosslink
    ├── derive/          # allocation, skeleton
    └── xlsx/            # the workbook editor and the layout map

payload/get-fsa-training-done/references/program/
├── overview.md
├── rules.md             # GENERATED
├── schemas.md           # GENERATED
├── examples/{mini,capstone}/
├── tasks/
└── workflows/
```

## Development

Two payload files are **generated**; edit the Python and regenerate:

```bash
python scripts/program/gen_rules_md.py
python scripts/program/gen_schemas_md.py
```

CI runs both with `--check`.

The clean example programme lives in the payload
([`references/program/examples/mini/`](../payload/get-fsa-training-done/references/program/examples/mini))
rather than in `tests/`, so the example the model reads and the fixture the
tests trust are the same bytes — and a consistency gate asserts it verifies with
zero errors *and* zero warnings. Failing cases are produced by copying it and
making one targeted edit. A second example,
[`examples/capstone/`](../payload/get-fsa-training-done/references/program/examples/capstone), is a project module graded
by three sprint reviews and a final review.

The workbook tests run against a synthetic form built in-test, since the vendor
template cannot be committed. Point `FSA_PROGRAM_TEMPLATE` at a real copy to run
the same checks against it:

```bash
FSA_PROGRAM_TEMPLATE=~/path/Template_Import_Syllabus.xlsx pytest tests/features/program
```

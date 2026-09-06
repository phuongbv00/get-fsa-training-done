# `assess` — the `fsa-assess` skill

Design and grade FSA training assessments. The agent authors the content; the
CLI does everything deterministic — deriving platform import files, checking
that the numbers add up, rendering PDFs, and running the mechanical half of
grading.

| | |
| --- | --- |
| Namespace | `assess` |
| Installed as | `fsa-assess` |
| Worker commands | `fsa-trainer-skills assess <verb>` |
| Payload | [`payload/fsa-assess/`](payload/fsa-assess) |

```bash
fsa-trainer-skills install --skill assess --platform all
```

## Assessment types

| Type | Produces |
| --- | --- |
| `quiz` | master question CSV + Blooket import |
| `short_assignment` | learner brief + instructor rubric + PDF (1–2 days) |
| `long_assignment` | learner brief + instructor rubric + PDF (3+ days) |
| `theory_exam` | master question CSV + Coderbyte import |
| `practice_exam` | learner brief + instructor rubric + PDF (timed) |
| `capstone_project` | topic brief + project spec + rubric + PDF |

Each type has a design workflow the agent follows
([`references/workflows/design/`](payload/fsa-assess/references/workflows/design))
and a matching verifier checklist
([`references/verifiers/`](payload/fsa-assess/references/verifiers)).

## Levels

Every assessment is calibrated for exactly one **level**, a required Step 0
input. It sets the default Bloom mix, difficulty mix, duration, task count,
how much of the specification is handed over, and how strict the rubric is.

| Level | Audience | Re/Un/Ap/An | E/M/H | Tasks |
| --- | --- | --- | --- | --- |
| `CPL` | intern | 30/40/30/0 | 50/35/15 | 3–4 |
| `FR` | fresher | 15/30/40/15 | 30/45/25 | 4–6 |
| `UP_SKILL` (junior) | junior moving toward mid | 5/25/45/25 | 20/45/35 | 4–6 |
| `UP_SKILL` (mid) | mid-level | 0/15/45/40 | 15/40/45 | 4–6 |
| `UP_SKILL` (senior) | senior | 0/10/40/50 | 10/35/55 | 3–5 |
| `RE_SKILL` (junior) | junior new to this stack | 10/30/45/15 | 25/45/30 | 4–6 |
| `RE_SKILL` (mid) | mid-level new to this stack | 5/20/45/30 | 20/40/40 | 4–6 |
| `RE_SKILL` (senior) | senior new to this stack | 0/15/40/45 | 15/35/50 | 3–5 |

Two axes, because they answer different questions. **`UP_SKILL`** is the same
stack at greater depth — the candidate already works here, and the assessment
probes how far. **`RE_SKILL`** is an experienced engineer arriving from a
*different* stack: transferable reasoning is high but stack-specific recall is
not assumed, so these lean on migration and integration framing and never
reward knowing an idiom by heart.

These are defaults, not rules. Step 0 confirms them with the user, and
`verify` reports drift from the level default as a warning rather than an
error.

```bash
fsa-trainer-skills assess levels show
fsa-trainer-skills assess levels show --level UP_SKILL --band mid --count 40
```

Percentages become whole questions by largest remainder, so counts always sum
to the requested total — ask the CLI rather than doing the arithmetic.

## Worker commands

### `emit` — derive import files

Platform import files are always *derived* from the master CSV, never written
by hand, so they cannot drift from the answer key.

```bash
fsa-trainer-skills assess emit blooket --master jpl_quiz_03.csv
fsa-trainer-skills assess emit coderbyte --master jpl_theory_01.csv -o custom.json
```

Formats are `blooket` (→ `_blooket.csv`) and `coderbyte` (→ `_coderbyte.json`).
The output path defaults to the master's name with that suffix.

### `verify` — machine-checkable shape

Whether the files hold together, whether the numbers add up, and whether the
bytes survive a platform import. Whether the questions are any *good* is the
verifier agent's job.

```bash
fsa-trainer-skills assess verify --type quiz \
  --master jpl_quiz_03.csv --blooket jpl_quiz_03_blooket.csv

fsa-trainer-skills assess verify --type long_assignment \
  --brief brief.md --rubric rubric.md --pdf brief.pdf --level UP_SKILL --band mid
```

Long-form takes `--brief`, `--rubric`, `--pdf`, `--spec`, `--max-pages`;
question sets take `--master`, `--blooket`, `--coderbyte`, `--expect-count`,
`--time-map`.

Passing `--level`/`--band` adds the calibration checks: the Bloom and
difficulty mix of a question set, and the task count of a long-form
assessment, are compared against that level's defaults. Drift is reported as a
**warning, never an error** — Step 0 may legitimately override any default, so
the run still passes. One question of slack per bucket absorbs rounding. A
level also supplies the right `--time-map` when you do not pass one, which
matters for non-quiz formats: `UP_SKILL` and `RE_SKILL` expect 30/45/75
seconds, not the 5/10/20 a quiz uses.

### `sprint-kit` — the capstone's learner pack

A capstone runs in sprints, and a sprint boundary is only a checkpoint if
something is due and something happens when it is missing. The gates, the
calendar, and the templates teams fill are all *derived from the project spec*,
for the same reason import files are derived from the master: written by hand,
the deadline in the spec and the deadline in the handout drift within a week.

```bash
fsa-trainer-skills assess sprint-kit --spec jpl_capstone_project_01_spec.md \
  --drive-root MKP-F26 --lang en --update-spec
```

Writes four files into `<stem>_sprint_kit/`:

| File | Audience |
|---|---|
| `SUBMISSION_GUIDE.md` | teams — calendar with real deadlines, the five gates, a tick-box checklist per sprint |
| `backlog_template.csv` | teams — the frozen-backlog column header with example rows |
| `sprint_review_template.md` | teams — the sprint review record skeleton |
| `spec_sprint_checkpoint.md` | the spec's own `## Sprint checkpoint` section |

`--update-spec` writes that last one into the spec directly. The gate wording
lives once, in `core/sprintkit.py`, so the handout a team reads, the section
`verify` checks, and the caps the rubric applies cannot disagree — a test
asserts the gate ids match `verify/capstone.py`, and regenerating the canonical
fixture spec must be a no-op.

The command refuses to run against a sprint calendar that fails verification,
and warns when `--drive-root` is left at its `<CLASS>` placeholder.

`--lang` picks the language, `en` by default, from the `Locale` table in
`core/sprintkit.py`. A language is added by adding a `Locale`, never by
translating the output — a hand-edited pack is no longer derived from the spec,
which is the only thing keeping the handout, the spec's checkpoint section, and
the rubric's caps in agreement. Gate ids stay `G1`–`G5` in every locale, so
`verify` and the caps work unchanged; a test asserts that for every locale, and
another asserts each locale's handout still carries the same dates, paths, and
filenames.

The per-sprint **instructor** form is deliberately not generated: it is
instructor-only, and emitting it beside three learner-facing files is how it
ends up in the same shared folder. Its template is in the payload, at
`references/sprint_checkpoint_template.md` §2.

### `render` — brief to PDF

```bash
fsa-trainer-skills assess render brief.md -o brief.pdf
```

Renders an A4 PDF and checks it against a page budget derived from the brief's
`Duration` header at two pages per hour. `--lang` sets the document language,
`en` by default and `vi` for a translated brief. Rendering a file whose name marks it as an instructor rubric
requires `--allow-rubric`, so a rubric is not handed out by accident.

### `grade` — the mechanical half

No command here runs learner code, and scoring judgement stays with the model.

| Subcommand | Does |
| --- | --- |
| `preprocess` | extract and normalise raw uploads against the roster |
| `plan` | split preprocessed submissions into grading batches |
| `aggregate` | roll per-submission score JSONs into one grade CSV |
| `quiz` | score a quiz platform report workbook |
| `plagiarism` | similarity across submissions (**instructor-only**) |
| `ai-cheat` | AI-authorship and shared-source signals (**instructor-only**) |

```bash
fsa-trainer-skills assess grade preprocess \
  --roster roster.csv --src ./uploads --subject JPL --type ASSIGNMENT

fsa-trainer-skills assess grade aggregate --scores ./scores --out grades.csv
```

`plagiarism` and `ai-cheat` collect observable signals for a human to review.
They prove nothing and must never change a grade on their own.

### `levels` — the calibration table

```bash
fsa-trainer-skills assess levels show --level RE_SKILL --band senior
fsa-trainer-skills assess levels show --json
```

## Prerequisites

`fsa-trainer-skills doctor` checks both:

- a Chromium-family browser, for `render`
- an archive extractor (`ditto`, `unzip`, `bsdtar`, `7z`, or `unar`), for
  `grade preprocess`

## Layout

```
skills/assess/
├── commands/            # CLI verbs: render, verify, emit, sprint-kit, grade, levels
├── core/                # the logic behind them
│   ├── levels.py        # calibration source of truth
│   ├── emit/            # blooket, coderbyte, master
│   ├── sprintkit.py     # capstone sprint gates and the learner pack
│   └── verify/
└── payload/fsa-assess/  # what gets installed into the agent
    ├── SKILL.md
    └── references/
        ├── levels.md    # GENERATED — see below
        ├── workflows/{design,grade}/
        └── verifiers/
```

## Development

`payload/fsa-assess/references/levels.md` is **generated** from
`core/levels.py` — the model reads the Markdown, the CLI reads the Python, and
writing both by hand would guarantee they drift. Edit the Python, then:

```bash
python scripts/assess/gen_levels_md.py
```

CI runs `--check` and fails when it is stale.

Skill-specific tests live in `tests/skills/assess/`, with canonical fixtures in
`tests/fixtures/assess/` (master CSVs, derived import files, a brief/rubric
pair). CI byte-compares `emit` output against those fixtures, so regenerate
them deliberately — never to make a failing test pass.

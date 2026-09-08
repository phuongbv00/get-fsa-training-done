# Workflow — practice exam

Timed, sat in one sitting. Everything from `short_assignment.md` applies; this
file covers only what differs.

**Produces:** `<stem>.md`, `<stem>_rubric.md`, `<stem>.pdf`

Read `references/workflows/design/short_assignment.md` first for the brief and
rubric shape, then apply the differences below.

## What changes

### Banner and code

`Code: <LEVEL>_<SUBJ>_PE_<seq>`, and `Duration:` is wall-clock ("2 hours").

### The page budget is binding

Two A4 pages per hour, floor of two. A two-hour exam gets four pages. This is
the constraint that matters most here, because reading time comes out of working
time: a brief the candidate cannot absorb and act on inside the slot is a defect
however good its content is.

`FSA assessment render` fails the build when it overruns. Cut content — do not shrink the
font or the margins.

### Feasibility is the design problem

Everything asked for has to be buildable, by this level of candidate, inside the
stated time, on a machine with no prepared scaffolding. Before finalising,
budget the tasks in minutes and check they sum to less than the duration with
room to spare. A candidate reads, thinks, sets up, builds, and checks; only the
building part is what you estimated.

When it does not fit, cut a whole task rather than thinning every task. Five
shallow tasks assess less than three real ones.

### Task shape

Prose-heavy tasks are the most common failure in exam briefs specifically,
because there is no time to parse them. Lead with bullets, always. Reserve the
one paragraph per task for the rule that carries the real difficulty.

### Caps carry more weight

In the rubric, a missing foundation should cap the whole task rather than
deducting from it — under time pressure candidates skip foundations first, and
a cap is what stops a broken-but-broad submission outscoring a correct narrow
one. Apply the level's rubric posture from `references/levels.md`.

## Verify

```bash
FSA assessment render "<output_dir>/<stem>.md"
FSA assessment verify --type practice_exam \
  --brief  "<output_dir>/<stem>.md" \
  --rubric "<output_dir>/<stem>_rubric.md" \
  --pdf    "<output_dir>/<stem>.pdf" \
  --level  "<LEVEL>"
```

`--level` takes the band with it for the banded levels — `UP_SKILL:mid`,
`RE_SKILL:senior` — and the level alone for `CPL` and `FR`.

Then run `references/verifiers/practice_exam.md`, which additionally asks for a
realistic per-task minute budget.

## Translated variant

Only if the user explicitly asks. `<stem>_<lang>.md` — `_vn` for Vietnamese —
with bilingual `##` headings, and code, identifiers, HTTP status codes, and
framework terms left in English. Render it too, with `FSA assessment render --lang vi`,
and hold it to the same budget.
**Never** produce a translated rubric: `verify` and the grading pipeline parse
the rubric's headings, so the instructor rubric stays English.

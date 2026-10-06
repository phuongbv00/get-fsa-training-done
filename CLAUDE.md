# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`get-fsa-training-done` ships **one agent skill** and the CLI behind it, and the two must stay in sync:

- **The skill** — installed as `get-fsa-training-done`, defined in `src/get_fsa_training_done/skill.py`, with its payload at `src/get_fsa_training_done/payload/get-fsa-training-done/`. It has three **features** dividing one job: `program` (curriculum, schedules, syllabi, vendor workbooks), `material` (lecture notes, handbooks, lab guides and worksheets), and `assessment` (quizzes, assignments, exams, capstones, grading).
- **The CLI** — `get-fsa-training-done`, with the alias `gftd`. Lifecycle commands (`install`, `update`, `uninstall`, `status`, `doctor`, `env`) act on the one skill; each feature's worker commands live under its namespace: `get-fsa-training-done <namespace> <verb>` (e.g. `get-fsa-training-done assessment render`).

The project was renamed from an earlier package that shipped three separate skills (see the README's upgrade note). The rename was a clean break, and `tests/test_consistency.py` keeps the old names out of everything but `CHANGELOG.md` and `README.md`.

## How the three features relate

A programme's `<TOPIC>_ScheduleDetail.csv` has a `Training Materials / Logistics & General Notes` column, and **that column is the manifest binding the three**. A row says a session exists, runs 90 minutes, serves objective `FEF-K1`, and will be served by a file called `fef_lab_01.md`.

- `program` declares the **slot** — that it exists, what it weighs, what will fill it.
- `material` produces `fef_lab_01.md`; `assessment` produces `dbf_quiz_01.csv`.

No feature authors another's artifact. Each verifies its own half of the manifest and, when a finding is really about someone else's file, names the feature that owns it. Keep that boundary when adding checks: `program verify` reports a missing *slot*, `material coverage` reports a missing *material*, and neither writes the other's file.

## Commands

```bash
pip install -e .                          # dev install
pytest                                    # run all tests
pytest tests/features/assessment/test_emit.py -q   # one file
ruff check . && ruff format --check .     # lint (CI enforces both)
python scripts/sync_version.py --check    # version consistency gate
for g in scripts/*/gen_*.py; do python "$g" --check; done   # generated references
```

When iterating on worker commands locally, `get-fsa-training-done --no-venv <cmd>` (or `GET_FSA_TRAINING_DONE_NO_VENV=1`) runs in the current interpreter instead of re-execing into the managed venv.

## Architecture

### Layout

```
src/get_fsa_training_done/
  cli.py  skill.py  errors.py  __about__.py
  lifecycle/   commands/ install/ platforms/ envmgr/ skillmeta.py   — puts the skill on disk
  features/    program/ material/ assessment/ common/                — the worker namespaces
  payload/get-fsa-training-done/                                     — what is installed
```

### CLI: lifecycle vs feature workers

- **Lifecycle** commands run in whatever interpreter invoked them — they must work before any environment exists — and act on `skill.SKILL`; there is no `--skill`.
- **Feature workers** — `features/__init__.py` lists `FEATURES`; each feature package exports `NAMESPACE`, `add_parsers(subparsers)` and optionally `doctor_extra()`. Workers re-exec via `lifecycle/envmgr/reexec` into a managed virtualenv keyed by `SKILL.dep_group`, bootstrapped on first use. The package is never installed into the venv — its parent dir goes on `PYTHONPATH`. The **package** declares zero runtime dependencies; the libraries the workers need are declared in `lifecycle/envmgr/requirements/core.txt` and pre-warmed by `install`.
- **No feature shells out to an external binary**, with two optional, allow-listed exceptions (`BINARY_ALLOWLIST` in `tests/test_consistency.py`): a `.rar` extractor in `grade preprocess`, because `.rar` has no pure-Python reader, and Docker in `features/assessment/core/sandbox.py`, because running code that is not ours — an exam's seed script, a submission's tests — needs a container. The sandbox's safety rules (no network, read-only source copied to tmpfs, CPU/memory/pids/time limits, `--rm`, resolver-only prefetch) live in that module, not in a workflow.

Each feature owns its `core/`, `commands/` and `README.md`; `features/common/` holds only what more than one feature reads (the finding shape, the level table). Detailed per-feature documentation belongs in that `README.md`, not the root one.

### The payload: tasks and workflows

```
SKILL.md                          router: per feature, a Workflows table and a Tasks table
references/common/                style.md, language_vn.md, tasks/ shared by every feature
references/<feature>/overview.md  naming, standing rules, report-back for that feature
references/<feature>/tasks/       one step each
references/<feature>/workflows/   ordered lists of tasks with per-type parameters
```

A **task** has a fixed contract — `# Task — <name>`, then `## Inputs`, `## Produces`, `## Steps`, `## Done when`, `## Hands off to` — and lists its own inputs so it can run alone when the user asks for one step. A **workflow** sequences tasks and never re-explains one. `tests/test_consistency.py` enforces the contract, that SKILL.md links every task and workflow file, that every backticked `references/...` path exists, and that every `FSA <word>` code span is a lifecycle command or a feature namespace. Put a new rule in the task it governs, not in a workflow.

Writing rules that apply to every feature (plain words, digits, tone, the example account `PhuongBV3`, the Vietnamese conventions) live once in `references/common/`.

### Generated files — never edit by hand

- `references/assessment/levels.md` ← `features/common/levels.py`, by `scripts/assessment/gen_levels_md.py`.
- `references/program/rules.md` ← `features/program/core/rules.py`, and `references/program/schemas.md` ← `core/schemas.py` + `core/schedule.py`, by `scripts/program/`.
- `references/material/structure.md` ← `features/material/core/grammar.py` + `core/rules.py`, by `scripts/material/gen_structure_md.py`.
- The version is canonical in `src/get_fsa_training_done/__about__.py`; `scripts/sync_version.py` propagates it to `package.json` and the payload's `VERSION`.
- `npm/python/` is a staged copy of `src/get_fsa_training_done` created by `npm/lib/prepack.js`. Regenerate it; never edit it.

Every `scripts/<feature>/gen_*.py` is covered by one globbed gate in `tests/test_consistency.py` and one loop in CI.

### Feature contract (program)

**No programme constant is ever hardcoded.** The reference pipeline this replaces carried seven modules, 280 hours, 70 days, a 240-minute training day, `W1..W14` and `D1..D96` as literals. All of them derive: the module table gives the codes and totals, `total_hours × 60 / total_days` gives the length of a training day, and the CSV headers give the calendar's width. When a figure cannot be derived the sources disagree — that is a finding, not a number to choose. Genuine policy (pass mark, first weekday, chapter span, creator, item patterns) is a flag instead.

Derived tables are never typed by hand: `derive allocation` computes a syllabus's §8 from its session plan and `derive skeleton` writes the CSV headers and row order from the module table. The rulebook lives once, in `core/rules.py`. An assessment item is matched to the sessions delivering it by **occurrence** — the item plus its ordinal — so a long assignment spread over several rows counts as one and `Quiz 1`/`Quiz 2` count as two; a project module's `Sprint Review` ×3 and `Final Review` are matched the same way (`examples/capstone/`).

`export` **edits** a copy of the vendor workbook with `zipfile` + `xml.etree` rather than rebuilding it: populated sheets are rewritten and every other part is copied byte-identically, so the writer never touches `styles.xml` and an over-long plan is refused. The vendor templates are the customer's property: never committed, and `.xlsx` only.

### Feature contract (material)

The template a lecture note follows lives once, in `core/grammar.py`, and `structure.md` is generated from it — prose describing a rule the checker does not enforce would calibrate the model to a constraint nothing holds it to. That is why diagram conventions are rules (`MAT-D19` cardinality in words, `MAT-D20` theme colours) rather than advice.

`material coverage` reads a programme's `ScheduleDetail` **by column name, tolerating any superset**, and deliberately does not enforce that CSV's schema — that is `program verify`'s job.

### Feature contract (assessment)

Platform import files are always *derived* from the master CSV (`assessment emit`), and `assessment verify` checks master ↔ import consistency. A capstone's sprint pack is derived from the spec's sprint table by `assessment sprint-kit`, so the gate wording lives once per language in `core/sprintkit.py`. A quiz or theory exam has two forms; `verify` tells them apart by the files given (`--master` vs `--brief`/`--rubric`), and `--answer-template` checks a written exam's answer sheet, including that it never repeats the questions. Instructor rubrics stay English because `verify` and the grading pipeline parse their headings. Calibration is keyed by **level** (`CPL`, `FR`, `UP_SKILL`/`RE_SKILL` with bands) in `features/common/levels.py`; drift is a **warning, never an error**.

Grading never runs learner code on the host; a rubric's behaviour check runs through `assessment sandbox`. Retake policy (`grade merge-retake`: cap 6, keep higher, voided retakes) is flags with defaults, never constants.

## Tests

An autouse fixture in `tests/conftest.py` redirects `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `GET_FSA_TRAINING_DONE_HOME`, and `XDG_CACHE_HOME` into a tmp dir — install tests create and delete skill folders, and this keeps them off the developer's real `~/.claude`. Keep any new test that touches install paths or the env cache under that isolation. Lifecycle tests live in `tests/lifecycle/`, feature tests in `tests/features/<namespace>/`, and payload-wide gates in `tests/test_consistency.py`. `assessment`'s canonical fixtures live in `tests/fixtures/assessment/` and CI byte-compares `emit` output against them; the sandbox's Docker test is skipped when Docker or the postgres image is absent.

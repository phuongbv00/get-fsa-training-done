# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`get-fsa-training-done` ships a CLI plus a registry of agent skills, all of which must stay in sync:

- **A skill registry** — each skill is a subpackage under `src/get_fsa_training_done/skills/` exporting a module-level `SKILL: Skill` object. Currently three, dividing one job: `skills/program/` (`fsa-training-program`, the curriculum, schedules, syllabi and vendor workbooks), `skills/material/` (`fsa-training-material`, lecture notes, handbooks and lab guides), and `skills/assessment/` (`fsa-training-assessment`, quizzes, exams, assignments and grading).
- **The `get-fsa-training-done` CLI** — shared lifecycle commands (`install`, `update`, `uninstall`, `status`, `doctor`, `env`) that operate across every registered skill, plus each skill's own worker commands under `get-fsa-training-done <namespace> <verb>` (e.g. `get-fsa-training-done assessment render`).

## How the three skills relate

A programme's `<TOPIC>_ScheduleDetail.csv` has a `Training Materials / Logistics & General Notes` column, and **that column is the manifest binding the three**. A row says a session exists, runs 90 minutes, serves objective `FEF-K1`, and will be served by a file called `fef_lab_01.md`.

- `program` declares the **slot** — that it exists, what it weighs, what will fill it.
- `material` produces `fef_lab_01.md`; `assessment` produces `dbf_quiz_01.csv`.

No skill authors another's artifact. Each verifies its own half of the manifest and, when a finding is really about someone else's file, names the skill that owns it. Keep that boundary when adding checks: `program verify` reports a missing *slot*, `material coverage` reports a missing *material*, and neither writes the other's file.

## Commands

```bash
pip install -e .                          # dev install
pytest                                    # run all tests
pytest tests/features/assessment/test_emit.py -q   # one file
ruff check . && ruff format --check .     # lint (CI enforces both)
python scripts/sync_version.py --check    # version consistency gate, every skill
python scripts/assessment/gen_levels_md.py --check   # assess skill's levels.md gate
```

When iterating on worker commands locally, `get-fsa-training-done --no-venv <cmd>` (or `GET_FSA_TRAINING_DONE_NO_VENV=1`) runs in the current interpreter instead of re-execing into the managed venv.

## Architecture

### CLI: lifecycle vs skill worker commands

`cli.py` builds its parser from two sources:

- **Lifecycle** (`install`, `update`, `uninstall`, `status`, `doctor`, `env`) run in whatever interpreter invoked them — they must work before any environment exists. They act across every skill by default, or one via `--skill <namespace>`.
- **Per-skill workers** — each `Skill.add_worker_parsers()` registers its own verbs under its own namespace. `assessment` registers `render`, `verify`, `emit`, `grade`, `levels` under `get-fsa-training-done assessment <verb>`. Workers re-exec via `envmgr.reexec` into a managed virtualenv keyed by the skill's `dep_group`, bootstrapped on first use. The package itself is never installed into the venv — its parent dir goes on `PYTHONPATH`. The **package** declares zero runtime dependencies (`pip install` pulls nothing, and every lifecycle command runs on a bare interpreter); the libraries the workers need live in the managed venv, declared in `envmgr/requirements/core.txt` and pre-warmed by `install`. **No skill shells out to an external binary** — the sole exception is a `.rar` extractor, which is optional because `.rar` has no pure-Python reader.

### The skill abstraction

`skillkit.Skill` (mirroring `platforms.base.Platform`) is the contract: `name` (installed identity, e.g. `"fsa-training-assessment"`), `namespace` (CLI prefix, e.g. `"assess"`), `payload_dir`, `dep_group`, `add_worker_parsers()`, `doctor_extra()`. `skills/__init__.py` discovers registered skills by scanning its subpackages for a `SKILL` object — adding a skill means adding a subpackage, nothing else. Each skill owns its own `core/`, `commands/`, and `README.md` under `skills/<namespace>/`; only `errors.py` is genuinely shared. Detailed per-skill documentation belongs in that `README.md`, not the root one, which covers only the CLI and the registry table that links to it. `install/` holds the plan/apply/receipt machinery, `platforms/` the Claude/Codex install targets — both skill-agnostic.

### Generated files — never edit by hand

- `src/get_fsa_training_done/skills/assessment/payload/fsa-training-assessment/references/levels.md` is generated from `skills/assessment/core/levels.py` by `scripts/assessment/gen_levels_md.py`. Edit the Python, then regenerate.
- `src/get_fsa_training_done/skills/program/payload/fsa-training-program/references/rules.md` is generated from `skills/program/core/rules.py`, and `references/schemas.md` from `core/schemas.py` + `core/schedule.py`, by the scripts in `scripts/program/`.
- `src/get_fsa_training_done/skills/material/payload/fsa-training-material/references/structure.md` is generated from `skills/material/core/grammar.py` by `scripts/material/gen_structure_md.py`.
- The version is canonical in `src/get_fsa_training_done/__about__.py`; `scripts/sync_version.py` iterates the skill registry and propagates it to `package.json` and every skill's payload `VERSION` file — adding a skill needs no edit to this script.

Every `scripts/<skill>/gen_*.py` is covered by one globbed gate in `tests/test_consistency.py` and one loop in CI, so a new skill's generated reference is checked the day it lands.
- `npm/python/` is a staged copy of `src/get_fsa_training_done` created by `npm/lib/prepack.js` (the npm package is a thin shim over the Python implementation). Regenerate it; never edit it.

CI (`consistency` job and `tests/test_consistency.py`) fails on drift in any of these. The top-level `tests/test_consistency.py` holds cross-skill gates (payload validity against Codex's rules, no duplicate skill names/namespaces, version sync); assess-specific gates (every assessment type has a workflow and verifier, SKILL.md links every workflow file) live in `tests/features/assessment/test_consistency.py`.

### Skill/CLI contract (program)

**No programme constant is ever hardcoded.** The reference pipeline this replaces (a Node script in a separate repo) carried seven modules, 280 hours, 70 days, a 240-minute training day, a 16800-minute total, `W1..W14` and `D1..D96` as literals, and worked for exactly one cohort. All of them derive: the module table gives the codes and totals, `total_hours × 60 / total_days` gives the length of a training day, and the CSV headers give the calendar's width. When a figure cannot be derived the sources disagree — that is a finding, not a number to choose. Genuine policy (pass mark, first weekday, chapter span, creator, item patterns) is a flag instead.

Derived tables are never typed by hand, for the same reason `assessment emit` exists: `derive allocation` computes a syllabus's §8 from its session plan and `derive skeleton` writes the CSV headers and row order from the module table. `verify` re-checks the same arithmetic, so a derived file passes by construction.

The rulebook lives once, in `core/rules.py`; bodies live in `core/checks/` and `references/rules.md` is generated from it. An assessment item is matched to the sessions delivering it by **occurrence** — the item plus its ordinal — so a long assignment spread over kickoff/completion/acceptance rows counts as one and `Quiz 1`/`Quiz 2` count as two, which is what removed the reference pipeline's two topic-code special cases.

`export` **edits** a copy of the vendor workbook with `zipfile` + `xml.etree` rather than rebuilding it: the populated sheets are rewritten and every other part is copied through byte-identically. Measured on the real form, an openpyxl round trip loses the classification label, the custom properties and the print setup, and the Node pipeline emitted 17 of 35 parts. Consequently the writer never touches `styles.xml` — it reuses each cell's existing style and cannot invent formatting — and the session-plan band is a fixed height with the summary block below it, so an over-long plan is refused rather than allowed to overwrite it. The vendor templates are the customer's property: never committed, and `.xlsx` only.

### Skill/CLI contract (material)

The template a lecture note follows lives once, in `core/grammar.py`, and `references/structure.md` is generated from it — prose describing a required section the checker does not enforce would calibrate the model to a constraint nothing holds it to.

`material coverage` is the cross-skill check: it reads a programme's `ScheduleDetail` **by column name, tolerating any superset**, and deliberately does not enforce that CSV's schema — that is `program verify`'s job. Each skill enforces only what it owns, so there is no shared constant and no duplicated rulebook.

Everything defaults to English; a Vietnamese translation is a separate `_vn` sibling artifact, matching the corpus convention, never a rewrite of the original.

### Skill/CLI contract (assessment)

Platform import files are always *derived* from the master CSV (`get-fsa-training-done assessment emit`), never written by hand, and `get-fsa-training-done assessment verify` checks master ↔ import consistency. A capstone's sprint pack follows the same rule: `get-fsa-training-done assessment sprint-kit` derives the learner handout, the templates, and the spec's `## Sprint checkpoint` section from the project spec's sprint table, so the gate wording lives once per language in `skills/assessment/core/sprintkit.py` and cannot drift from the ids `core/verify/capstone.py` enforces. English is the default for everything the skill emits and other languages are available on request; for the sprint pack that means a `Locale` in `sprintkit.py` (`--lang`, currently `en` and `vi`) rather than translating generated output, and instructor rubrics stay English in every case because `verify` and the grading pipeline parse their headings. Assessment calibration (Bloom mix, difficulty, duration, rubric posture) is keyed by **level** (`CPL`, `FR`, `UP_SKILL`/`RE_SKILL` with `junior`/`mid`/`senior` bands) defined once in `skills/assessment/core/levels.py`. `verify --level/--band` compares the artifact against that level via `core/verify/calibration.py` and reports drift as a **warning, never an error** — Step 0 may legitimately override any default.

## Tests

An autouse fixture in `tests/conftest.py` redirects `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `GET_FSA_TRAINING_DONE_HOME`, and `XDG_CACHE_HOME` into a tmp dir — install tests create and delete skill folders, and this keeps them off the developer's real `~/.claude`. Keep any new test that touches install paths or the env cache under that isolation. `tests/test_install.py` parametrizes its whole lifecycle matrix over a `skill` fixture built from `skill_registry.all_skills()`, so a new skill gets the same coverage automatically. Skill-specific tests live under `tests/features/<namespace>/`; `assessment`'s canonical fixtures live in `tests/fixtures/assessment/` (master CSVs, derived import files, the long-form brief/rubric pair) and CI byte-compares `emit` output against them.

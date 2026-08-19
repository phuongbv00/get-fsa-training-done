# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Repositioned as `fsa-trainer-skills`, a multi-skill repo.** The single
  `fsa-assess` package and CLI are now a shared `fsa-trainer-skills` CLI over a
  registry of independent skills; `fsa-assess` is the first one registered,
  reached under `fsa-trainer-skills assess <verb>` instead of `fsa-assess
  <verb>`. Lifecycle commands (`install`, `update`, `uninstall`, `status`) gain
  `--skill <namespace>` (default: every registered skill) and print one
  section per skill. Adding a skill is additive: a subpackage under
  `src/fsa_trainer_skills/skills/` exporting a `SKILL` object, picked up by the
  registry automatically — no edits to `cli.py`, the lifecycle commands, or
  `scripts/sync_version.py`.
- Every CLI-owned identifier renamed along with it: the `fsa-assess` skill's
  own identity (its `name`, payload directory, and SKILL.md frontmatter) is
  unchanged, but the package, the binary, `FSA_ASSESS_*` env vars (now
  `FSA_TRAINER_SKILLS_*`), the install receipt (`.fsa-trainer-skills-
  install.json`), the venv stamp, and the cache directory are all
  `fsa-trainer-skills` now, with no back-compat aliasing.
- The capstone project's display-code abbreviation is now `PRJ` (was `CP`), so
  new capstone codes read `<LEVEL>_<SUBJ>_PRJ_<seq>`. Filename stems, archive
  tokens, and every other type's abbreviation are unchanged.

### Fixed

- **`verify --level` and `--band` were parsed and thrown away.** They sat in a
  `calibration` argument group and `run()` never read them, so the calibration
  the workflows and `references/levels.md` promise was never actually checked.
  They now drive `core/verify/calibration.py`, which compares a question set's
  Bloom and difficulty mix against the level's defaults and a long-form
  assessment's task count against the level's range. Drift is a **warning,
  never an error** — Step 0 may legitimately override any default — and one
  question of slack per bucket absorbs largest-remainder rounding. Passing a
  level also supplies the right `--time-map` when none is given, which matters
  for non-quiz formats: `UP_SKILL`/`RE_SKILL` expect 30/45/75 seconds rather
  than a quiz's 5/10/20. `--band` without `--level` is now an error instead of
  being silently ignored.
- **`status` invented a second install when the two scopes named one
  directory.** Run from the directory holding the user-scope config — the home
  directory, normally — `<cwd>/.claude/skills` *is* `~/.claude/skills`, so the
  same install was described once per scope and `status` reported four rows for
  two installs. Rows are now deduplicated by resolved destination, keeping the
  scope examined first.
- `install/receipt.py`'s `cli_invocation()` looped over two identical
  candidate names (`("fsa-assess", "fsa-assess")`), a leftover from an
  earlier find-and-replace. There was never a second distinct candidate;
  replaced with a single `which(CLI_NAME)` check.

### Removed

- The `entry_test` assessment type, end to end: its design workflow, verifier,
  blueprint template, `verify --type entry_test`, and the Question Bank
  delivery formats (`emit qb-csv` / `emit qb-xlsx`) that existed only for it.
  With `qb-xlsx` gone the openpyxl `xlsx` dependency group, its vendored
  wheels, and the `[xlsx]` extra are gone too — the CLI now has no third-party
  code paths at all.

## [0.1.1] — 2026-08-18

### Fixed

- **Coderbyte multi-answer questions marked a wrong option correct.** The
  emitter kept the master's option order and listed every correct index, but
  Coderbyte treats index 0 as correct whether or not it appears in
  `correctAnswers` — its own template shows `["2", "3"]` over
  `["I am correct", "Wrong 2", "Will be correct", "Will be correct"]`, meaning
  0, 2 and 3. So any question whose first option was wrong shipped with that
  option marked correct, and the import accepted it silently. A correct option
  now always leads, and `correctAnswers` lists every correct index, which
  therefore always includes `"0"`. Single-answer output is unchanged.
- `verify --type theory_exam` now rejects that shape: it requires `"0"` among
  `correctAnswers` and compares the option *text* at each listed index against
  the master's key, so a mismatch cannot hide behind a reordering.

## [0.1.0] — 2026-08-18

### Added

- `fsa-assess` CLI with `install`, `update`, `uninstall`, `status`, `doctor`,
  and `env` commands, targeting Claude Code and the Codex CLI at both user and
  project scope.
- Install receipts (`.fsa-assess-install.json`) written inside the installed
  skill directory, so `update` and `uninstall` keep working on a hand-copied
  install and never touch files the user edited.
- A managed virtualenv, created on first use and provisioned from vendored
  wheels, so worker commands always run against pinned dependencies and work
  offline.
- npm distribution as a thin shim over the Python implementation.

### Assessment types

- Seven design types: `short_assignment`, `long_assignment`, `practice_exam`,
  `quiz`, `theory_exam`, `entry_test`, and `capstone_project` — the last two
  new, replacing artifacts that had been authored by hand outside any workflow.
- Level calibration across `CPL`, `FR`, `UP_SKILL`, and `RE_SKILL`, the latter
  two banded junior/mid/senior, driving the Bloom mix, difficulty mix, duration,
  scope, and rubric posture.
- `emit` derives every platform import file from the master question CSV, so the
  Blooket CSV, Coderbyte JSON, and Question Bank CSV/XLSX cannot drift from the
  answer key.

### Grading

- `preprocess`, `plan`, `aggregate`, `quiz`, `plagiarism`, and `ai-cheat`,
  ported from the previous project-scoped skill with every path made explicit.

### Fixed while porting

- `aggregate` treated only `dropped` as dropped while three other scripts also
  accepted `inactive`, so an `inactive` trainee was skipped everywhere and then
  reappeared in the grade CSV.
- Student ids were recovered with `name.split("_")[-1]`, silently truncating any
  roster id containing an underscore.
- Similarity fingerprints used the builtin `hash()`, which Python randomises per
  process, so a flagged pair could never be re-checked in a later run.
- Quiz nicknames that matched no roster id were dropped from the output without
  a word; they are now reported.
- The rubric task-list parser scanned the whole document, double-counting every
  task for a rubric whose score sheet puts the id in its own cell.
- `plan_batches` accepted `--subject` and `--type` and ignored both.

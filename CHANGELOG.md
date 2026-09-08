# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`fsa-training-program` (`program`) — design a training programme and export
  its workbooks.** Replaces a Node pipeline that lived in a separate repository
  and worked for exactly one cohort: it carried seven modules, 280 hours, 70
  days, a 240-minute training day, a 16800-minute total, `W1..W14` and `D1..D96`
  as literals. **Every one of those now derives** — the module table gives the
  codes and totals, `total_hours × 60 / total_days` gives the length of a
  training day, and the CSV headers give the calendar's width. When a figure
  cannot be derived the sources disagree, which is a finding rather than a
  number to pick.
  - `program verify` reconciles the curriculum, the four schedules and every
    syllabus/session-plan pair against each other. 36 rules, each carrying an id
    into a generated `references/rules.md`.
  - `program derive` computes what must not be typed twice: a syllabus's Time
    Allocation from its session plan, and the four CSV skeletons from the module
    table.
  - `program export syllabus` fills the FPT vendor workbook by **editing** a
    copy of the template with `zipfile` and `xml.etree` — the populated sheets
    are rewritten and every other part is copied through byte-identically. On
    the real form that preserves 32 of 35 parts (losing only the calc chain and
    the form's dead identity sheet), where an openpyxl round trip drops the
    classification label, the custom properties and the print setup, and the
    Node pipeline emitted 17.
  - The reference pipeline special-cased two topic codes; matching an assessment
    item to the sessions delivering it by **occurrence** — the item plus its
    ordinal — removes both. A long assignment spread over kickoff, completion
    and acceptance rows is one assignment; `Quiz 1` and `Quiz 2` are two.
- **`fsa-training-material` (`material`) — write the teaching material a session
  plan calls for.** Lecture notes, module handbooks, appendices, and the
  step-by-step lab guides the corpus was missing entirely.
  - `material verify` checks a document against the template its filename
    claims: one title on line 1, no front matter, an objectives section,
    contiguous section numbers, a language tag on every fence, and every link
    and `#anchor` resolving. 22 rules, with a generated `references/structure.md`.
  - `material coverage` is the cross-skill check. A session plan's materials
    column names the file serving each session, so it reports both what is
    promised and missing and what is present and unscheduled — counting files
    that belong to another skill as such rather than as gaps.
  - `material derive appendix` rebuilds the appendix's syllabus map, whose deep
    anchors are the only ones in a module and break silently when a heading is
    renamed.

### Changed

- **BREAKING: the skill is renamed `fsa-training-assessment`, under the
  `assessment` namespace** (was `fsa-assess` / `assess`), making room for a
  family of three: `fsa-training-program` and `fsa-training-material` follow.
  Every worker command moves with it — `fsa-trainer-skills assessment render`,
  `... assessment grade`, and so on.
- **A rename orphans the old install, so `install` and `update` now clear it.**
  The installed directory is named after the skill, and hosts load every
  directory under `skills/` — so a stale `fsa-assess` folder would keep
  advertising the same "ra đề" / "chấm điểm" triggers as the new skill and the
  agent would see two skills competing for one request. `Skill.previous_names`
  drives the cleanup, which removes exactly what the old receipt vouches for and
  keeps any file you edited, the same rule `uninstall` follows. `status` and
  `doctor` report a superseded install when they find one.
- **No skill shells out to an external binary any more.** The libraries the
  workers need live in the managed venv (`envmgr/requirements/core.txt`), which
  `install` pre-warms; the package itself still declares zero dependencies, so
  the offline guarantee holds after the first install rather than before it. A
  consistency gate fails the build if a skill reaches for `subprocess` or
  `shutil.which` again.
- **`assessment render` no longer needs Chrome.** It renders with `xhtml2pdf`
  in-process and **embeds its own fonts**, so a Vietnamese brief comes out
  identical everywhere instead of depending on the host's installed faces.
  *This changes existing output:* `xhtml2pdf` implements less print CSS than
  Chrome — `break-inside` and `break-after` are ignored — so a brief may land on
  a different number of pages than before. The page budget itself is unchanged.
  The `--chrome` flag is gone.
- **`assessment grade preprocess` no longer needs an archive extractor.** `.zip`
  and `.tar*` are read with the standard library and `.7z` with `py7zr`.
  Extraction now refuses entries that would escape the trainee's folder, which
  the shell tools used to handle for us. `.rar` is the one exception — it is
  proprietary with no pure-Python reader — and still uses `unar`, `7z`, or
  `bsdtar` when one is on `PATH`; `doctor` reports it as optional and no longer
  fails when no extractor is present.
- The level table moved to `fsa_trainer_skills/levels.py`, shared beside
  `errors.py`, since a programme code carries a level segment too. Behaviour is
  unchanged. The finding/report value type moved to `fsa_trainer_skills/findings.py`
  for the same reason — two skills check many artifacts in one run and need a
  finding to name where it was found and which rule fired. The rule ids stay
  private to each skill; only the shape is shared.
- The generated-reference gate is now globbed over `scripts/*/gen_*.py`, in both
  the test suite and CI, so a new skill's generated payload file is covered the
  day it lands rather than when someone remembers to add it.
- Payload workflows now write `FSA assessment <verb>` for worker commands.
  `FSA` is the bare CLI: worker verbs take a namespace and lifecycle commands do
  not, so the old mix of `FSA verify` and `FSA doctor` could not both be right.
  A gate now checks every `FSA <word>` in a payload resolves to something real.

### Fixed

- **The page-budget check could reject a brief that was within budget.**
  `count_pages` took the largest `/Count` anywhere in the PDF, but `/Count` also
  appears in the outline tree, where it counts bookmarks — one per heading. A
  one-page brief with eight headings reported eight pages. It now reads `/Count`
  only from a `/Type /Pages` node.

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

- **The design workflows could not verify a banded level.** Every long-form
  workflow passed `--level "<LEVEL>"` alone, which `verify` rejects for
  `UP_SKILL` and `RE_SKILL` (`needs a band`), and the quiz and theory-exam
  workflows passed no `--level` at all, so the calibration check never ran for
  a question set. `--level` now accepts the band in the key — `UP_SKILL:mid`,
  the same form as `Level.id` — and every workflow passes it; the level also
  supplies the time map, so the explicit `--time-map` is only needed when the
  confirmed map differs.
- **`emit` accepted a master `verify` rejects.** `emit/master.py` read up to
  six `Answer N` columns while `verify` and the workflow require exactly the
  twelve-column header with four filled answers. The extended-master path is
  gone: `emit` enforces the same header and the same four options, and the
  option-count warnings that only that path could trigger are gone with it.
- **`grade preprocess` silently dropped loose-file uploads.** Only archives
  and folders were gathered, so a bare PDF or a single source file was skipped
  without a word and its trainee reported as "did NOT submit". Loose files are
  now copied into the trainee's folder like any other upload. A trainee whose
  only archive failed to extract was also listed under "did NOT submit"; the
  failure line is now the only report.
- `grade ai-cheat` documented a `--keyboard-chars` flag that did not exist;
  the docstring and the unused `charset` plumbing are removed.
- `grade plagiarism` stripped comments before string literals, so a `//` in a
  URL literal (or a `#` in a Python string) swallowed the rest of the line.
  Strings and comments are now matched in one left-to-right pass.
- `assess render` defaulted to `--lang vi`; it is `en`, like everything else
  the skill emits, with `vi` for a translated brief.
- The capstone verifier read "each sprint 2 weeks long" as a reference to
  Sprint 2; the reference pattern is now the capitalised proper noun only.
- `doctor` exited non-zero when no browser was found, although only `render`
  needs one; it is reported but no longer fails the check. `doctor` also
  enumerates every dependency group rather than a hard-coded `core`.
- `SKILL.md` jumped from Step 0 to Step 2; routing is now Step 1, and the
  CLI-resolution section says to fall through when a receipt written on
  another machine names an interpreter that is not there.
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

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`fsa-trainer-skills` ships a CLI plus a registry of agent skills, all of which must stay in sync:

- **A skill registry** — each skill is a subpackage under `src/fsa_trainer_skills/skills/` exporting a module-level `SKILL: Skill` object. Currently one: `skills/assess/`, the `fsa-assess` skill (design and grade FSA training assessments).
- **The `fsa-trainer-skills` CLI** — shared lifecycle commands (`install`, `update`, `uninstall`, `status`, `doctor`, `env`) that operate across every registered skill, plus each skill's own worker commands under `fsa-trainer-skills <namespace> <verb>` (e.g. `fsa-trainer-skills assess render`).

## Commands

```bash
pip install -e .                          # dev install
pytest                                    # run all tests
pytest tests/skills/assess/test_emit.py -q   # one file
ruff check . && ruff format --check .     # lint (CI enforces both)
python scripts/sync_version.py --check    # version consistency gate, every skill
python scripts/assess/gen_levels_md.py --check   # assess skill's levels.md gate
```

When iterating on worker commands locally, `fsa-trainer-skills --no-venv <cmd>` (or `FSA_TRAINER_SKILLS_NO_VENV=1`) runs in the current interpreter instead of re-execing into the managed venv.

## Architecture

### CLI: lifecycle vs skill worker commands

`cli.py` builds its parser from two sources:

- **Lifecycle** (`install`, `update`, `uninstall`, `status`, `doctor`, `env`) run in whatever interpreter invoked them — they must work before any environment exists. They act across every skill by default, or one via `--skill <namespace>`.
- **Per-skill workers** — each `Skill.add_worker_parsers()` registers its own verbs under its own namespace. `assess` registers `render`, `verify`, `emit`, `grade`, `levels` under `fsa-trainer-skills assess <verb>`. Workers re-exec via `envmgr.reexec` into a managed virtualenv keyed by the skill's `dep_group`, bootstrapped on first use. The package itself is never installed into the venv — its parent dir goes on `PYTHONPATH`. The project has **zero runtime dependencies**.

### The skill abstraction

`skillkit.Skill` (mirroring `platforms.base.Platform`) is the contract: `name` (installed identity, e.g. `"fsa-assess"`), `namespace` (CLI prefix, e.g. `"assess"`), `payload_dir`, `dep_group`, `add_worker_parsers()`, `doctor_extra()`. `skills/__init__.py` discovers registered skills by scanning its subpackages for a `SKILL` object — adding a skill means adding a subpackage, nothing else. Each skill owns its own `core/`, `commands/`, and `README.md` under `skills/<namespace>/`; only `errors.py` is genuinely shared. Detailed per-skill documentation belongs in that `README.md`, not the root one, which covers only the CLI and the registry table that links to it. `install/` holds the plan/apply/receipt machinery, `platforms/` the Claude/Codex install targets — both skill-agnostic.

### Generated files — never edit by hand

- `src/fsa_trainer_skills/skills/assess/payload/fsa-assess/references/levels.md` is generated from `skills/assess/core/levels.py` by `scripts/assess/gen_levels_md.py`. Edit the Python, then regenerate.
- The version is canonical in `src/fsa_trainer_skills/__about__.py`; `scripts/sync_version.py` iterates the skill registry and propagates it to `package.json` and every skill's payload `VERSION` file — adding a skill needs no edit to this script.
- `npm/python/` is a staged copy of `src/fsa_trainer_skills` created by `npm/lib/prepack.js` (the npm package is a thin shim over the Python implementation). Regenerate it; never edit it.

CI (`consistency` job and `tests/test_consistency.py`) fails on drift in any of these. The top-level `tests/test_consistency.py` holds cross-skill gates (payload validity against Codex's rules, no duplicate skill names/namespaces, version sync); assess-specific gates (every assessment type has a workflow and verifier, SKILL.md links every workflow file) live in `tests/skills/assess/test_consistency.py`.

### Skill/CLI contract (assess)

Platform import files are always *derived* from the master CSV (`fsa-trainer-skills assess emit`), never written by hand, and `fsa-trainer-skills assess verify` checks master ↔ import consistency. A capstone's sprint pack follows the same rule: `fsa-trainer-skills assess sprint-kit` derives the learner handout, the templates, and the spec's `## Sprint checkpoint` section from the project spec's sprint table, so the gate wording lives once per language in `skills/assess/core/sprintkit.py` and cannot drift from the ids `core/verify/capstone.py` enforces. English is the default for everything the skill emits and other languages are available on request; for the sprint pack that means a `Locale` in `sprintkit.py` (`--lang`, currently `en` and `vi`) rather than translating generated output, and instructor rubrics stay English in every case because `verify` and the grading pipeline parse their headings. Assessment calibration (Bloom mix, difficulty, duration, rubric posture) is keyed by **level** (`CPL`, `FR`, `UP_SKILL`/`RE_SKILL` with `junior`/`mid`/`senior` bands) defined once in `skills/assess/core/levels.py`. `verify --level/--band` compares the artifact against that level via `core/verify/calibration.py` and reports drift as a **warning, never an error** — Step 0 may legitimately override any default.

## Tests

An autouse fixture in `tests/conftest.py` redirects `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `FSA_TRAINER_SKILLS_HOME`, and `XDG_CACHE_HOME` into a tmp dir — install tests create and delete skill folders, and this keeps them off the developer's real `~/.claude`. Keep any new test that touches install paths or the env cache under that isolation. `tests/test_install.py` parametrizes its whole lifecycle matrix over a `skill` fixture built from `skill_registry.all_skills()`, so a new skill gets the same coverage automatically. Skill-specific tests live under `tests/skills/<namespace>/`; `assess`'s canonical fixtures live in `tests/fixtures/assess/` (master CSVs, derived import files, the long-form brief/rubric pair) and CI byte-compares `emit` output against them.

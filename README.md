# fsa-trainer-skills

A CLI plus a registry of agent skills for FSA training tools, installable
into [Claude Code](https://claude.com/claude-code) and the
[Codex CLI](https://developers.openai.com/codex/cli).

The package ships one `fsa-trainer-skills` CLI over a registry of skills.
Lifecycle commands (`install`, `update`, `uninstall`, `status`, `doctor`,
`env`) are shared and act across every registered skill; each skill's own
worker commands live under its own namespace: `fsa-trainer-skills <namespace>
<verb>`. Adding a new skill is additive — a sibling namespace, no changes to
the shared commands.

Currently registered:

| Namespace | Skill | What it does | Docs |
| --- | --- | --- | --- |
| `program` | `fsa-training-program` | design a training programme and export its workbooks | [README](src/fsa_trainer_skills/skills/program/README.md) |
| `assessment` | `fsa-training-assessment` | design and grade FSA training assessments | [README](src/fsa_trainer_skills/skills/assessment/README.md) |

Every skill is **stateless**. It assumes nothing about the directory layout it
was installed into and never scans a project on a hunch — it asks for its
inputs first, echoes back the resolved paths, and waits for a go-ahead.

## Install

```bash
pip install fsa-trainer-skills
```

or

```bash
npm install -g fsa-trainer-skills
```

Both give you the same `fsa-trainer-skills` command. The npm package is a thin
shim that delegates to the Python implementation, so it needs Python 3.9+ on
`PATH`.

Then install every skill into your agent:

```bash
fsa-trainer-skills install --platform all
```

| Command | Effect |
| --- | --- |
| `fsa-trainer-skills install --platform claude --scope user` | `~/.claude/skills/<skill>` |
| `fsa-trainer-skills install --platform claude --scope project` | `./.claude/skills/<skill>` |
| `fsa-trainer-skills install --platform codex --scope user` | `~/.codex/skills/<skill>` |
| `fsa-trainer-skills install --platform codex --scope project` | `./.codex/skills/<skill>` |
| `fsa-trainer-skills update` | upgrade in place, preserving files you edited |
| `fsa-trainer-skills uninstall --platform all` | remove exactly what was installed |
| `fsa-trainer-skills status` | what is installed where, per skill, and whether it drifted |
| `fsa-trainer-skills doctor` | check this machine for every skill's prerequisites |

Add `--skill <namespace>` to target one skill instead of all of them, and
`--dry-run` to any of `install`, `update`, or `uninstall` to see the exact
file-by-file plan without touching anything.

## Skills

Each skill documents itself in its own `README.md` next to its code, rather
than in this file. That keeps the root README about the CLI and the registry,
and means adding a skill adds a file instead of editing a shared one.

- **[`program`](src/fsa_trainer_skills/skills/program/README.md)** — design a
  training programme: the curriculum and its schedules, the outcome-standard
  mapping, one syllabus and session plan per topic, and the vendor workbooks.
  Nothing is a constant: module counts, totals, the length of a training day and
  the calendar's width are all derived from the sources and checked against each
  other.
- **[`assessment`](src/fsa_trainer_skills/skills/assessment/README.md)** — design and
  grade FSA training assessments: quizzes, short and long assignments, theory
  and practice exams, and capstone projects, each calibrated by level, plus the
  grading pipeline.

## Dependencies

Every skill does its deterministic work in Python, and **no skill needs an
external binary**.

Installing the package pulls nothing: `dependencies = []` is deliberate, so the
lifecycle commands run on a bare interpreter. The libraries the worker commands
need live in the **managed virtualenv** instead — declared once in
`src/fsa_trainer_skills/envmgr/requirements/core.txt` and shared by every skill:

| Library | Used by |
| --- | --- |
| `xhtml2pdf` | `assessment render`, for the brief PDF |
| `py7zr` | `assessment grade preprocess`, for `.7z` submissions |

`fsa-trainer-skills install` builds that environment, so the first install needs
a network and everything after it does not — which is the property that matters
on an exam machine.

There is exactly one optional external tool. `.rar` is proprietary and has no
pure-Python reader, so a `.rar` submission needs `unar`, `7z`, or `bsdtar` on
`PATH`; every other archive format is read in-process. `fsa-trainer-skills
doctor` reports it as optional and never fails for its absence.

Rendering embeds its own fonts (see
[`core/fonts/`](src/fsa_trainer_skills/skills/assessment/core/fonts)), so a
Vietnamese brief comes out identical on every machine rather than depending on
which faces the host happens to have installed.

## Adding a skill

A skill is a subpackage under `src/fsa_trainer_skills/skills/` exporting a
module-level `SKILL: Skill` object (see `skills/assessment/__init__.py`). The
registry discovers it automatically — no edits to `cli.py`, the lifecycle
commands, or `scripts/sync_version.py` are needed. Give it its own
`payload/<skill-name>/` directory alongside its `core/`/`commands/` modules,
and its own `VERSION` file for `sync_version.py` to keep in sync.

Give it a `README.md` in that same directory documenting its commands and
conventions, and link it from the registry table above — detailed per-skill
docs do not belong in this file.

## Development

```bash
pip install -e .
pytest
python scripts/sync_version.py --check
for generator in scripts/*/gen_*.py; do python "$generator" --check; done
```

`src/fsa_trainer_skills/__about__.py` holds the canonical version;
`sync_version.py` propagates it to `package.json` and every registered
skill's payload `VERSION` file.

## Licence

MIT

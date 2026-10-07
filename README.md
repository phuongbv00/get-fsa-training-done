# get-fsa-training-done

One agent skill, and the CLI behind it, for getting FSA training done:
designing a programme, writing its teaching material, and designing and grading
its assessments. It installs into [Claude Code](https://claude.com/claude-code)
and the [Codex CLI](https://developers.openai.com/codex/cli).

The [landing page](https://phuongbv00.github.io/get-fsa-training-done/) shows
how it works, in real files; its source is in `docs/`.

The skill has three features, each with its own CLI namespace:

| Namespace | What it does | Docs |
| --- | --- | --- |
| `program` | design a training programme and export its workbooks | [README](src/get_fsa_training_done/features/program/README.md) |
| `material` | write lecture notes, handbooks, lab guides and worksheets | [README](src/get_fsa_training_done/features/material/README.md) |
| `assessment` | design and grade quizzes, assignments, exams and capstones | [README](src/get_fsa_training_done/features/assessment/README.md) |

They divide one job. A programme's session plan names, in its
`Training Materials` column, the file that serves each session — so `program`
declares that a slot exists and what it weighs, `material` writes the lecture
note or lab guide, and `assessment` writes the quiz, brief or exam. No feature
authors another's artifact, and each checks its own half of that manifest.

The skill is built from **tasks** — one step each, such as writing a rubric,
rendering a brief, or merging a retake — composed into **workflows**. Ask for a
whole job and the agent follows the workflow; ask for one step and it runs that
task on its own.

The skill is **stateless**. It assumes nothing about the directory layout it
was installed into and never scans a project on a hunch — it asks for its
inputs first, echoes back the resolved paths, and waits for a go-ahead.

## Install

```bash
pip install get-fsa-training-done
```

This gives you the `gftd` command, which every example below uses; it is also
installed under its full name, `get-fsa-training-done`.
It needs Python 3.12+.

Then install the skill into your agent:

```bash
gftd install --platform all
```

| Command | Effect |
| --- | --- |
| `gftd install --platform claude --scope user` | `~/.claude/skills/get-fsa-training-done` |
| `gftd install --platform claude --scope project` | `./.claude/skills/get-fsa-training-done` |
| `gftd install --platform codex --scope user` | `~/.codex/skills/get-fsa-training-done` |
| `gftd install --platform codex --scope project` | `./.codex/skills/get-fsa-training-done` |
| `gftd update` | upgrade in place, preserving files you edited |
| `gftd uninstall --platform all` | remove exactly what was installed |
| `gftd status` | what is installed where, and whether it drifted |
| `gftd doctor` | check this machine for the skill's prerequisites |

Add `--dry-run` to any of `install`, `update`, or `uninstall` to see the exact
file-by-file plan without touching anything.

## Dependencies

Installing the package pulls nothing: `dependencies = []` is deliberate, so the
lifecycle commands run on a bare interpreter. The libraries the worker commands
need live in the **managed virtualenv** instead — declared once in
`src/get_fsa_training_done/lifecycle/envmgr/requirements/core.txt`:

| Library | Used by |
| --- | --- |
| `xhtml2pdf` | `assessment render`, for the brief PDF |
| `py7zr` | `assessment grade preprocess`, for `.7z` submissions |

`gftd install` builds that environment, so the first install
needs a network and everything after it does not — which is the property that
matters on an exam machine.

Two external tools are optional, and `doctor` reports each without failing for
its absence:

- **A `.rar` extractor** (`unar`, `7z` or `bsdtar`). `.rar` is proprietary and
  has no pure-Python reader; every other archive format is read in-process.
- **Docker**, for `assessment sandbox`: running a seed script, a JUnit suite or
  a pytest run that is not ours — an exam's supplied files, or a submission —
  in a disposable container with no network.

Rendering embeds its own fonts (see
[`core/fonts/`](src/get_fsa_training_done/features/assessment/core/fonts)), so a
Vietnamese brief comes out identical on every machine.

## Layout

```
src/get_fsa_training_done/
  cli.py  skill.py          the CLI, and the one skill it installs
  lifecycle/                install, update, uninstall, status, doctor, env
  features/                 program, material, assessment (+ common)
  payload/get-fsa-training-done/
    SKILL.md                the router: workflows and tasks per feature
    references/<feature>/   overview, tasks/, workflows/, generated references
    references/common/      writing style, Vietnamese conventions, shared tasks
```

## Development

```bash
pip install -e .
pytest
ruff check . && ruff format --check .
python scripts/sync_version.py --check
for generator in scripts/*/gen_*.py; do python "$generator" --check; done
```

`src/get_fsa_training_done/__about__.py` holds the canonical version;
`sync_version.py` propagates it to the payload's `VERSION`.

## Licence

MIT

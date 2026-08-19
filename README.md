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

| Namespace | Skill | What it does |
| --- | --- | --- |
| `assess` | `fsa-assess` | design and grade FSA training assessments |

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

## The `assess` skill

Design and grade FSA training assessments. Its worker commands live under
`fsa-trainer-skills assess <verb>`:

| Type | Produces |
| --- | --- |
| `quiz` | master question CSV + Blooket import |
| `short_assignment` | learner brief + instructor rubric + PDF (1–2 days) |
| `long_assignment` | learner brief + instructor rubric + PDF (3+ days) |
| `theory_exam` | master question CSV + Coderbyte import |
| `practice_exam` | learner brief + instructor rubric + PDF (timed) |
| `capstone_project` | topic brief + project spec + rubric + PDF |

Every type is calibrated by **level** — `CPL`, `FR`, `UP_SKILL`, and `RE_SKILL`,
the latter two with `junior`/`mid`/`senior` bands — which sets the default Bloom
mix, difficulty mix, duration, scope depth, and rubric posture.

The agent authors content; the CLI does everything deterministic. Import files
are always *derived* from the master CSV rather than written by hand, which is
what keeps them from drifting apart:

```bash
fsa-trainer-skills assess emit blooket --master jpl_quiz_03.csv -o jpl_quiz_03_blooket.csv
fsa-trainer-skills assess verify --type quiz --master jpl_quiz_03.csv --blooket jpl_quiz_03_blooket.csv
```

It also drives grading:

```bash
fsa-trainer-skills assess grade preprocess --roster roster.csv --src ./uploads --subject JPL --type ASSIGNMENT
fsa-trainer-skills assess grade aggregate --scores ./scores --out grades.csv
```

## Dependencies

The CLI has **no** Python dependencies.

Two external binaries matter to the `assess` skill, and `fsa-trainer-skills
doctor` checks for both:

- a Chromium-family browser, for rendering briefs to PDF
- an archive extractor (`ditto`, `unzip`, `bsdtar`, `7z`, or `unar`), for
  unpacking submissions

## Adding a skill

A skill is a subpackage under `src/fsa_trainer_skills/skills/` exporting a
module-level `SKILL: Skill` object (see `skills/assess/__init__.py`). The
registry discovers it automatically — no edits to `cli.py`, the lifecycle
commands, or `scripts/sync_version.py` are needed. Give it its own
`payload/<skill-name>/` directory alongside its `core/`/`commands/` modules,
and its own `VERSION` file for `sync_version.py` to keep in sync.

## Development

```bash
pip install -e .
pytest
python scripts/sync_version.py --check
python scripts/assess/gen_levels_md.py --check
```

`src/fsa_trainer_skills/__about__.py` holds the canonical version;
`sync_version.py` propagates it to `package.json` and every registered
skill's payload `VERSION` file.

## Licence

MIT

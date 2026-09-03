"""`fsa-trainer-skills assess sprint-kit` — the learner-facing sprint pack.

Same contract as `emit`: the spec is the single source, and everything a team
receives is derived from it. Hand-writing the handout puts the sprint calendar
in three places — spec, handout, rubric — and they drift within a week.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..core import sprintkit


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "sprint-kit",
        help="generate the learner sprint handout and templates from a project spec",
        description=(
            "Derive the sprint pack a team receives — submission guide, per-sprint "
            "checklist, backlog and review templates — from the capstone project spec. "
            "Never hand-write these; regenerate them so the calendar and the gates "
            "cannot drift from what `verify` enforces."
        ),
    )
    parser.add_argument("--spec", required=True, help="capstone project spec markdown")
    parser.add_argument(
        "-o",
        "--out",
        help="output directory (default: <spec stem without _spec>_sprint_kit next to the spec)",
    )
    parser.add_argument(
        "--lang",
        default=sprintkit.DEFAULT_LANGUAGE,
        choices=list(sprintkit.LANGUAGES),
        help=(
            "language of the generated pack (default: en). The pack is generated, not "
            "translated by hand, so a new language means a new Locale in core/sprintkit.py"
        ),
    )
    parser.add_argument(
        "--drive-root",
        default="<CLASS>",
        help="Drive folder the team folders live under, e.g. MKP-F26 (default: <CLASS>)",
    )
    parser.add_argument(
        "--update-spec",
        action="store_true",
        help="also rewrite the spec's '## Sprint checkpoint' section from the same source",
    )
    parser.set_defaults(func=run)


def _default_out(spec_path: Path) -> Path:
    stem = spec_path.stem
    if stem.endswith("_spec"):
        stem = stem[: -len("_spec")]
    return spec_path.with_name(f"{stem}_sprint_kit")


def run(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec).expanduser()
    locale = sprintkit.locale_for(args.lang)
    project = sprintkit.read_project(spec_path)
    out_dir = Path(args.out).expanduser() if args.out else _default_out(spec_path)

    written = sprintkit.write_kit(project, out_dir, args.drive_root, locale)

    if args.update_spec:
        sprintkit.update_spec(spec_path, project, args.drive_root, locale)

    print(
        f"PASS: wrote {len(written)} files to {out_dir} for {len(project.sprints)} sprints "
        f"in {locale.code}"
    )
    for path in written:
        print(f"  {path}")
    if args.update_spec:
        print(f"  {spec_path} (## Sprint checkpoint rewritten)")
    else:
        print(
            "NOTE: paste spec_sprint_checkpoint.md into the spec's '## Sprint checkpoint' "
            "section, or re-run with --update-spec"
        )
    if args.drive_root == "<CLASS>":
        print(
            "WARNING: --drive-root not given, so the handout says <CLASS>; teams cannot "
            "find that folder"
        )
    return 0

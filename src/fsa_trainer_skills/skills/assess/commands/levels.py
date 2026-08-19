"""`fsa-trainer-skills assess levels` — print the calibration table the workflows read from."""

from __future__ import annotations

import argparse
import json

from fsa_trainer_skills.errors import UsageError

from ..core import levels as levels_mod


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "levels",
        help="show the level calibration table",
    )
    sub = parser.add_subparsers(dest="levels_command", required=True)

    show = sub.add_parser("show", help="print every level, or one in detail")
    show.add_argument("--level", help="CPL, FR, UP_SKILL, or RE_SKILL")
    show.add_argument("--band", choices=list(levels_mod.BANDS))
    show.add_argument(
        "--count",
        type=int,
        help="also show the question counts this level implies for a set of this size",
    )
    show.add_argument("--json", action="store_true", dest="as_json")
    show.set_defaults(func=run_show)


def run_show(args: argparse.Namespace) -> int:
    if args.level:
        try:
            selected = [levels_mod.resolve(args.level, args.band)]
        except levels_mod.UnknownLevel as exc:
            raise UsageError(str(exc)) from None
    else:
        selected = list(levels_mod.LEVELS)

    if args.as_json:
        payload = []
        for level in selected:
            entry = levels_mod.as_dict(level)
            if args.count:
                entry["counts"] = levels_mod.counts_for(level, args.count)
            payload.append(entry)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if len(selected) == 1:
        _print_detail(selected[0], args.count)
        return 0

    _print_table(selected)
    return 0


def _percentages(table: dict[str, int], order: tuple[str, ...]) -> str:
    return "/".join(str(table.get(name, 0)) for name in order)


def _print_table(levels: list[levels_mod.Level]) -> None:
    bloom_header = "/".join(name[:2] for name in levels_mod.BLOOM_ORDER)
    difficulty_header = "/".join(name[0] for name in levels_mod.DIFFICULTY_ORDER)
    print(f"{'level':<18} {'audience':<38} {bloom_header:<14} {difficulty_header:<10} tasks")
    print("-" * 92)
    for level in levels:
        print(
            f"{level.display:<18} {level.audience:<38} "
            f"{_percentages(level.bloom, levels_mod.BLOOM_ORDER):<14} "
            f"{_percentages(level.difficulty, levels_mod.DIFFICULTY_ORDER):<10} "
            f"{level.task_range[0]}-{level.task_range[1]}"
        )
    print(f"\nBloom order: {', '.join(levels_mod.BLOOM_ORDER)}")
    print(f"Difficulty order: {', '.join(levels_mod.DIFFICULTY_ORDER)}")
    print("Run with --level (and --band) for the full calibration of one level.")


def _print_detail(level: levels_mod.Level, count: int | None) -> None:
    print(f"{level.display} — {level.audience}\n")
    print(f"  scope            {level.scope}")
    print(f"  rubric posture   {level.rubric_posture}")
    print(
        "  mechanisms       "
        + (
            "may be named in the brief"
            if level.may_name_mechanism
            else "state the outcome; the candidate chooses the mechanism"
        )
    )
    print(f"  duration factor  {level.duration_factor}x the baseline")
    print(f"  tasks            {level.task_range[0]}-{level.task_range[1]} for long-form work")
    print("\n  Bloom mix")
    for name in levels_mod.BLOOM_ORDER:
        if level.bloom.get(name):
            print(f"    {name:<12} {level.bloom[name]:>3}%")
    print("\n  Difficulty mix")
    for name in levels_mod.DIFFICULTY_ORDER:
        if level.difficulty.get(name):
            print(f"    {name:<12} {level.difficulty[name]:>3}%")
    print("\n  Seconds per question (non-quiz formats)")
    for name in levels_mod.DIFFICULTY_ORDER:
        if name in level.time_map:
            print(f"    {name:<12} {level.time_map[name]:>3}s")

    if count:
        counts = levels_mod.counts_for(level, count)
        print(f"\n  For a {count}-question set")
        for axis in ("bloom", "difficulty"):
            rendered = ", ".join(f"{name} {value}" for name, value in counts[axis].items())
            print(f"    {axis:<12} {rendered}")

    if level.notes:
        print(f"\n  {level.notes}")

"""`get-fsa-training-done assessment verify` — structural checks on generated
assessment artifacts."""

from __future__ import annotations

import argparse

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.common import levels as levels_mod

from ..core.verify import (
    ALL_TYPES,
    CAPSTONE_TYPES,
    LONG_FORM_TYPES,
    QUESTION_SET_TYPES,
    CheckResult,
    long_form,
    question_set,
)
from ..core.verify.common import DEFAULT_TIME_MAP, parse_time_map


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "verify",
        help="check generated assessment artifacts for structural problems",
        description=(
            "Machine-verifiable shape only: whether the files hold together, whether "
            "the numbers add up, and whether the bytes will survive a platform import. "
            "Whether the questions are any good is the verifier agent's job."
        ),
    )
    parser.add_argument("--type", required=True, choices=list(ALL_TYPES))

    long_form_group = parser.add_argument_group("long-form (assignments, exams, capstone)")
    long_form_group.add_argument("--brief", help="learner brief markdown")
    long_form_group.add_argument("--rubric", help="instructor rubric markdown")
    long_form_group.add_argument("--pdf", help="rendered brief PDF, for the page-budget check")
    long_form_group.add_argument("--spec", help="capstone project spec markdown")
    long_form_group.add_argument(
        "--max-pages", type=int, help="override the duration-derived page budget"
    )

    question_group = parser.add_argument_group("question sets (quiz, theory exam)")
    question_group.add_argument("--master", help="master question CSV")
    question_group.add_argument("--blooket", help="generated Blooket CSV")
    question_group.add_argument("--coderbyte", help="generated Coderbyte JSON")
    question_group.add_argument(
        "--expect-count", type=int, help="assert the master holds exactly this many questions"
    )
    question_group.add_argument(
        "--time-map",
        default=None,
        help="expected time limit per difficulty, e.g. Easy=5,Medium=10,Hard=20 (default: 5/10/20)",
    )

    calibration = parser.add_argument_group("calibration")
    calibration.add_argument("--level", help="CPL, FR, UP_SKILL, or RE_SKILL")
    calibration.add_argument("--band", choices=("junior", "mid", "senior"))

    parser.set_defaults(func=run)


def resolve_level(args: argparse.Namespace) -> levels_mod.Level | None:
    """`--band` alone is a typo, not a request — say so rather than ignoring it."""
    if not args.level:
        if args.band:
            raise UsageError("--band needs --level")
        return None
    try:
        return levels_mod.resolve(args.level, args.band)
    except levels_mod.UnknownLevel as exc:
        raise UsageError(str(exc)) from None


def resolve_time_map(
    args: argparse.Namespace, level: levels_mod.Level | None = None
) -> dict[str, str]:
    """An explicit --time-map wins; otherwise the level knows the right one.

    Without a level we cannot do better than the quiz timings, which is what
    this defaulted to before levels were wired in.
    """
    if args.time_map:
        try:
            return parse_time_map(args.time_map)
        except ValueError as exc:
            raise UsageError(str(exc)) from None
    if level is not None:
        return levels_mod.time_map_for(level, args.type)
    return dict(DEFAULT_TIME_MAP)


def run(args: argparse.Namespace) -> int:
    result = CheckResult()
    level = resolve_level(args)

    if args.type in LONG_FORM_TYPES or args.type in CAPSTONE_TYPES:
        long_form.verify(
            assessment_type=args.type,
            brief_path=args.brief,
            rubric_path=args.rubric,
            pdf_path=args.pdf,
            max_pages=args.max_pages,
            result=result,
            level=level,
        )
        if args.type in CAPSTONE_TYPES:
            from ..core.verify import capstone

            capstone.verify(
                brief_path=args.brief,
                spec_path=args.spec,
                rubric_path=args.rubric,
                result=result,
            )

    elif args.type in QUESTION_SET_TYPES:
        question_set.verify(
            master_path=args.master,
            blooket_path=args.blooket,
            coderbyte_path=args.coderbyte,
            time_map=resolve_time_map(args, level),
            expect_count=args.expect_count,
            result=result,
            level=level,
        )

    return result.report(f"structural verification of the {args.type} artifacts")

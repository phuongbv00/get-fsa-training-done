"""`fsa-trainer-skills assess grade` — the mechanical half of grading.

Extraction, batching, aggregation, quiz arithmetic, and the instructor-only
cheat checks. The judgement — reading a submission against a rubric and deciding
a score — stays with the model, and no command here executes learner code.

Every path is an argument. Nothing is inferred from the working directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fsa_trainer_skills.errors import UsageError

from ..core import grading

aggregate_mod = grading.aggregate
ai_cheat_mod = grading.ai_cheat
batches_mod = grading.batches
plagiarism_mod = grading.plagiarism
preprocess_mod = grading.preprocess
quiz_mod = grading.quiz_scores
roster_mod = grading.roster


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "grade",
        help="preprocess, batch, aggregate, and check trainee submissions",
        description=(
            "The mechanical half of grading. Scoring judgement belongs to the model; "
            "no command here runs learner code."
        ),
    )
    sub = parser.add_subparsers(dest="grade_command", required=True)

    prep = sub.add_parser("preprocess", help="extract and normalise submissions")
    prep.add_argument("--roster", required=True, help="roster CSV with ID, Name, Status columns")
    prep.add_argument("--src", required=True, help="folder holding the raw uploads")
    prep.add_argument("--subject", required=True, help="subject code, e.g. JPL")
    prep.add_argument("--type", required=True, dest="submission_type", help="ASSIGNMENT, P_EXAM…")
    prep.add_argument("--out", help="output folder (default: <src>/_preprocessed)")
    prep.set_defaults(func=run_preprocess)

    plan = sub.add_parser("plan", help="split preprocessed submissions into grading batches")
    plan.add_argument("--preprocessed", required=True)
    plan.add_argument("--scores", required=True, help="folder holding per-submission score JSONs")
    plan.add_argument("--subject", required=True)
    plan.add_argument("--type", required=True, dest="submission_type")
    plan.add_argument("--roster", help="roster CSV, to exclude trainees who dropped")
    plan.add_argument("--batches", type=int, default=4)
    plan.add_argument("--include-scored", action="store_true")
    plan.set_defaults(func=run_plan)

    agg = sub.add_parser("aggregate", help="roll score JSONs into one grade CSV")
    agg.add_argument("--scores", required=True)
    agg.add_argument("--out", required=True, help="grade CSV to write")
    agg.add_argument("--roster", help="roster CSV, for names and row order")
    agg.add_argument("--order", help="file of student ids, one per line, for row order")
    agg.add_argument(
        "--include-dropped-ids",
        nargs="*",
        metavar="STD_ID",
        help="dropped trainees to include anyway",
    )
    agg.set_defaults(func=run_aggregate)

    quiz = sub.add_parser("quiz", help="score a quiz platform report")
    quiz.add_argument("--xlsx", required=True, help="quiz report workbook")
    quiz.add_argument("--out", required=True, help="score CSV to write")
    quiz.add_argument("--roster", help="roster CSV, to map nicknames and drop leavers")
    quiz.add_argument("--converted-csv", help="also write the raw sheet as CSV")
    quiz.add_argument("--sheet-index", type=int, default=2, help="1-based sheet (default: 2)")
    quiz.add_argument(
        "--list-unmatched",
        action="store_true",
        help="list every nickname that is not on the roster, however many there are",
    )
    quiz.set_defaults(func=run_quiz)

    plag = sub.add_parser("plagiarism", help="similarity across submissions (instructor-only)")
    plag.add_argument("--preprocessed", required=True)
    plag.add_argument("--out", required=True, help="output folder")
    plag.add_argument("--subject", required=True)
    plag.add_argument("--type", required=True, dest="submission_type")
    plag.add_argument("--threshold", type=float, default=plagiarism_mod.DEFAULTS["threshold"])
    plag.add_argument("--containment", type=float, default=plagiarism_mod.DEFAULTS["containment"])
    plag.add_argument("--k", type=int, default=plagiarism_mod.DEFAULTS["k"])
    plag.add_argument("--window", type=int, default=plagiarism_mod.DEFAULTS["window"])
    plag.add_argument("--min-tokens", type=int, default=plagiarism_mod.DEFAULTS["min_tokens"])
    plag.add_argument("--exts", help="comma-separated extensions overriding the defaults")
    plag.set_defaults(func=run_plagiarism)

    cheat = sub.add_parser(
        "ai-cheat",
        help="AI-authorship and shared-source signals (instructor-only)",
        description=(
            "Collects observable signals for a human to review. Proves nothing, and "
            "must never change a grade on its own."
        ),
    )
    cheat.add_argument("--preprocessed", nargs="+", required=True)
    cheat.add_argument("--out", required=True, help="output folder")
    cheat.add_argument("--subject", required=True)
    cheat.add_argument("--type", required=True, dest="submission_type")
    cheat.add_argument("--scores", nargs="*", help="score folders, to filter by --min-score")
    cheat.add_argument("--min-score", type=float, default=0.0)
    cheat.add_argument("--min-tokens", type=int, default=40)
    cheat.set_defaults(func=run_ai_cheat)


def _roster(path: str | None):
    return roster_mod.load(Path(path).expanduser()) if path else None


def run_preprocess(args: argparse.Namespace) -> int:
    src = Path(args.src).expanduser()
    if not src.is_dir():
        raise UsageError(f"source folder not found: {src}")
    out = Path(args.out).expanduser() if args.out else src / "_preprocessed"

    roster = roster_mod.load(Path(args.roster).expanduser())
    outcome = preprocess_mod.run(
        roster=roster,
        src=src,
        out=out,
        subject=args.subject,
        submission_type=args.submission_type,
    )

    subject = args.subject.upper()
    submission_type = args.submission_type.upper()
    print(f"# Preprocess: {subject} / {submission_type}")
    print(f"source: {src}")
    print(f"output: {out}\n")
    print(f"Created {len(outcome.created)} student folder(s):")
    for std_id, known, multiple in outcome.created:
        flags = []
        if not known:
            flags.append("UNKNOWN-ID (not on the roster)")
        if multiple:
            flags.append("multiple archives")
        suffix = f"  <- {', '.join(flags)}" if flags else ""
        print(f"  {roster_mod.folder_name(subject, submission_type, std_id)}{suffix}")

    if outcome.missing:
        print(f"\nDid NOT submit ({len(outcome.missing)}):")
        for std_id, name in outcome.missing:
            print(f"  {std_id}  ({name})")

    if outcome.skipped_dropped:
        print(f"\nSkipped submissions from trainees who dropped ({len(outcome.skipped_dropped)}):")
        for std_id, source_name in outcome.skipped_dropped:
            print(f"  {std_id}  <- {source_name}")

    if outcome.failures:
        print(f"\nExtraction FAILED ({len(outcome.failures)}):")
        for name, info in outcome.failures:
            print(f"  {name}: {info}")
        return 1
    return 0


def run_plan(args: argparse.Namespace) -> int:
    scores = Path(args.scores).expanduser()
    scores.mkdir(parents=True, exist_ok=True)
    plan = batches_mod.plan(
        preprocessed=Path(args.preprocessed).expanduser(),
        scores=scores,
        roster=_roster(args.roster),
        subject=args.subject,
        submission_type=args.submission_type,
        batch_count=args.batches,
        include_scored=args.include_scored,
    )
    print(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False))
    return 0


def run_aggregate(args: argparse.Namespace) -> int:
    out = Path(args.out).expanduser()
    result = aggregate_mod.aggregate(
        scores_dir=Path(args.scores).expanduser(),
        roster=_roster(args.roster),
        order_path=Path(args.order).expanduser() if args.order else None,
        include_dropped=args.include_dropped_ids,
    )
    legend_path = aggregate_mod.write(result, out)

    print(result.legend)
    if result.skipped_dropped:
        print(
            f"\nExcluded {len(result.skipped_dropped)} dropped trainee(s): "
            + ", ".join(sorted(result.skipped_dropped))
        )
    print(f"\nWrote {len(result.rows)} row(s) -> {out}")
    print(f"Legend -> {legend_path}")
    return 0


def run_quiz(args: argparse.Namespace) -> int:
    xlsx = Path(args.xlsx).expanduser()
    out = Path(args.out).expanduser()
    rows = quiz_mod.read_sheet(xlsx, args.sheet_index)

    if args.converted_csv:
        converted = Path(args.converted_csv).expanduser()
        quiz_mod.write_csv(converted, rows)
        print(f"Converted sheet {args.sheet_index} -> {converted}")

    roster = _roster(args.roster)
    result = quiz_mod.score(rows, roster)
    quiz_mod.write_csv(out, result.rows)

    if result.dropped:
        print(f"Excluded {len(result.dropped)} dropped trainee(s)")

    if result.unmatched:
        # These people sat the quiz but are not on this roster. Usually that just
        # means the report covers the whole cohort and they belong to another
        # class — so say so rather than raising an alarm — but a mistyped
        # nickname looks identical, and silently dropping it would lose a real
        # score. Report the count always, the names on request.
        print(
            f"NOTE: {len(result.unmatched)} nickname(s) are not on this roster and were "
            "left out of the score CSV."
        )
        if args.list_unmatched or len(result.unmatched) <= 5:
            for nickname in result.unmatched:
                print(f"    {nickname}")
        else:
            print("      re-run with --list-unmatched to see them")
        print(
            "      Expected if this report covers several classes; otherwise one of them "
            "is a mistyped nickname worth reconciling by hand."
        )

    print(f"Wrote {result.scored} score row(s) -> {out}")
    return 0


def run_plagiarism(args: argparse.Namespace) -> int:
    extensions = None
    if args.exts:
        extensions = {
            item if item.startswith(".") else "." + item
            for item in (part.strip().lower() for part in args.exts.split(","))
            if item
        }

    report = plagiarism_mod.run(
        preprocessed=Path(args.preprocessed).expanduser(),
        subject=args.subject,
        submission_type=args.submission_type,
        extensions=extensions,
        threshold=args.threshold,
        containment=args.containment,
        k=args.k,
        window=args.window,
        min_tokens=args.min_tokens,
    )
    json_path, text_path = plagiarism_mod.write(report, Path(args.out).expanduser())
    print(report.text)
    print(f"Wrote {json_path} and {text_path}")
    return 0


def run_ai_cheat(args: argparse.Namespace) -> int:
    report = ai_cheat_mod.run(
        preprocessed=[Path(path).expanduser() for path in args.preprocessed],
        subject=args.subject,
        submission_type=args.submission_type,
        score_dirs=[Path(path).expanduser() for path in (args.scores or [])],
        min_score=args.min_score,
        min_tokens=args.min_tokens,
    )
    json_path, text_path = ai_cheat_mod.write(report, Path(args.out).expanduser())
    print(report.text)
    print(f"Wrote {json_path} and {text_path}")
    return 0

"""`gftd assessment grade` — the mechanical half of grading.

Extraction, batching, aggregation, retake merges, quiz arithmetic, and the
instructor-only cheat checks. The judgement — reading a submission against a
rubric and deciding a score — stays with the model, and no command here executes
learner code; `assessment sandbox` is where that happens, in a container.

Every path is an argument. Nothing is inferred from the working directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from ..core import grading

aggregate_mod = grading.aggregate
ai_cheat_mod = grading.ai_cheat
batches_mod = grading.batches
fams_practice_mod = grading.fams_practice
fams_theory_mod = grading.fams_theory
plagiarism_mod = grading.plagiarism
preprocess_mod = grading.preprocess
quiz_mod = grading.quiz_scores
quiz_module_mod = grading.quiz_module
retake_mod = grading.retake
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

    retake = sub.add_parser(
        "merge-retake",
        help="merge a first-attempt grade CSV with a retake's",
        description=(
            "Keep one result per trainee. The retake total is capped, the higher "
            "effective total wins by default, and a voided retake leaves the first "
            "attempt standing. The attempt kept supplies the task scores and comment."
        ),
    )
    retake.add_argument("--first", required=True, help="first-attempt grade CSV")
    retake.add_argument("--retake", required=True, help="retake grade CSV")
    retake.add_argument("--out", required=True, help="merged grade CSV to write")
    retake.add_argument("--roster", help="roster CSV, for row order and names")
    retake.add_argument(
        "--cap",
        type=float,
        default=retake_mod.DEFAULT_CAP,
        help=f"most a retake can earn (default: {retake_mod.DEFAULT_CAP:g})",
    )
    retake.add_argument(
        "--keep",
        choices=retake_mod.KEEP_POLICIES,
        default="higher",
        help="keep the higher effective total, or always the retake (default: higher)",
    )
    retake.add_argument(
        "--void-ids",
        nargs="*",
        default=[],
        metavar="STD_ID",
        help="trainees whose retake was cancelled; their first attempt stands",
    )
    retake.add_argument(
        "--cap-note",
        default=retake_mod.DEFAULT_CAP_NOTE,
        help="comment added when the cap applies; {cap} is replaced (write it in the "
        "comment language)",
    )
    retake.set_defaults(func=run_merge_retake)

    ingest = sub.add_parser(
        "quiz-ingest", help="add a quiz report or leaderboard to a module's results CSV"
    )
    ingest_source = ingest.add_mutually_exclusive_group(required=True)
    ingest_source.add_argument("--xlsx", help="quiz report workbook")
    ingest_source.add_argument(
        "--html", action="append", help="Blooket leaderboard HTML (repeatable)"
    )
    ingest.add_argument("--results", required=True, help="the module's results CSV (appended)")
    ingest.add_argument("--quiz", required=True, help="the quiz's column label, e.g. 'JCF 01'")
    ingest.add_argument("--part", default="", help="which run of the quiz: live, HW…")
    ingest.add_argument("--sheet-index", type=int, default=2, help="1-based sheet (default: 2)")
    ingest.set_defaults(func=run_quiz_ingest)

    module = sub.add_parser(
        "quiz-score", help="score every quiz in a module's results CSV, by roster"
    )
    module.add_argument("--results", required=True, help="the module's results CSV")
    module.add_argument("--roster", required=True, help="roster CSV")
    module.add_argument(
        "--questions",
        type=int,
        help="questions per quiz, for rows without an unattempted count (leaderboards, "
        "screenshots)",
    )
    module.add_argument(
        "--questions-for",
        action="append",
        default=[],
        metavar="LABEL=N",
        help="a quiz whose question count differs from --questions (repeatable)",
    )
    module.add_argument(
        "--alias",
        action="append",
        default=[],
        metavar="NICK=STD_ID",
        help="map a nickname the roster cannot match to a roster id (repeatable)",
    )
    module.add_argument("--out", required=True, help="score CSV to write")
    module.set_defaults(func=run_quiz_score)

    export = sub.add_parser("export", help="grades into a platform's import file")
    export_sub = export.add_subparsers(dest="export_target", required=True, metavar="<target>")
    fams = export_sub.add_parser("fams", help="into one of FAMS's two mark templates")
    # FAMS's two mark templates, named as FAMS names them. Each takes the class
    # template downloaded from FAMS, which decides who is in the class, or,
    # without one, the roster.
    fams_sub = fams.add_subparsers(dest="fams_template", required=True, metavar="<template>")
    theory = fams_sub.add_parser(
        "theory",
        help="quiz or theory-exam marks, FAMS's theory mark template: one row per test",
        description=(
            "Fill FAMS's theory mark template, which quizzes and the theory exam share: "
            "one row per trainee per test, a final mark only."
        ),
    )
    theory_source = theory.add_mutually_exclusive_group(required=True)
    theory_source.add_argument(
        "--quiz-scores", help="`grade quiz-score` output: a module's quizzes"
    )
    theory_source.add_argument(
        "--grades", help="`grade aggregate` or `merge-retake` output: a written theory exam"
    )
    _fams_arguments(theory)
    theory.add_argument(
        "--assessment",
        action="append",
        default=[],
        metavar="[LABEL=]CODE",
        help="a test's code on FAMS: CODE for one test, LABEL=CODE per quiz (repeatable; "
        "default: Quiz_<n> by column order, or the template's TestName for --grades)",
    )
    theory.set_defaults(func=run_export_fams_theory)

    practice = fams_sub.add_parser(
        "practice",
        help="assignment or practice-exam marks, FAMS's practice mark template: a mark per task",
        description=(
            "Fill FAMS's practice mark template, which the assignments and the practice exam "
            "share: one row per trainee, a mark per task over the task weights."
        ),
    )
    practice.add_argument(
        "--grades", required=True, help="`grade aggregate` or `merge-retake` output"
    )
    _fams_arguments(practice)
    practice.add_argument(
        "--assessment",
        help="the assessment's code on FAMS, e.g. Assignments_1 (default: the template's)",
    )
    practice.add_argument("--marker", help="the marker's FPT account (default: the template's)")
    practice.add_argument(
        "--date", help=f"marking date (default: today, {fams_practice_mod.DATE_FORMAT})"
    )
    practice.add_argument(
        "--pass-mark", type=float, default=6.0, help="generated form only (default: 6)"
    )
    practice.add_argument(
        "--missing-comment",
        default=fams_practice_mod.MISSING_COMMENT,
        help="comment for a trainee with no grade row, in the comments' language",
    )
    practice.add_argument("--mark-label", help="header over the mark column")
    practice.set_defaults(func=run_export_fams_practice)

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


def _fams_arguments(parser: argparse.ArgumentParser) -> None:
    """What both FAMS forms take."""
    parser.add_argument("--roster", required=True, help="roster CSV: FPT accounts, CPL emails")
    parser.add_argument("--template", help="the class's template downloaded from FAMS")
    parser.add_argument("--topic-code", help="e.g. FR_JSKS_JCF (default: the template's)")
    parser.add_argument("--out", required=True, help=".xlsx to write")


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


def _aliases(values: list[str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for value in values:
        nickname, sep, std_id = value.partition("=")
        if not sep or not nickname.strip() or not std_id.strip():
            raise UsageError(f"--alias takes NICK=STD_ID, got {value!r}")
        aliases[nickname.strip()] = std_id.strip()
    return aliases


def run_merge_retake(args: argparse.Namespace) -> int:
    out = Path(args.out).expanduser()
    merged = retake_mod.merge(
        retake_mod.read(Path(args.first).expanduser()),
        retake_mod.read(Path(args.retake).expanduser()),
        cap=args.cap,
        keep=args.keep,
        void=args.void_ids,
        cap_note=args.cap_note,
        roster=_roster(args.roster),
    )
    retake_mod.write(merged, out)
    print(f"Retake kept for {len(merged.from_retake)} trainee(s)")
    if merged.capped:
        print(f"Capped at {args.cap:g}: {', '.join(merged.capped)}")
    if merged.voided:
        print(f"Retake voided, first attempt kept: {', '.join(merged.voided)}")
    for note in merged.notes:
        print(f"NOTE: {note}")
    print(f"Wrote {len(merged.rows)} row(s) -> {out}")
    return 0


def run_quiz_ingest(args: argparse.Namespace) -> int:
    results = Path(args.results).expanduser()
    if args.html:
        rows = [list(quiz_mod.LEADERBOARD_HEADERS)]
        for path in args.html:
            # The question count is applied when the module is scored.
            rows += quiz_mod.read_leaderboard(Path(path).expanduser(), 1)[1:]
        for row in rows[1:]:
            row[4] = ""
    else:
        rows = quiz_mod.read_sheet(Path(args.xlsx).expanduser(), args.sheet_index)
    added = quiz_module_mod.from_report(rows, args.quiz.strip(), args.part.strip())
    quiz_module_mod.append_results(results, added)
    print(f"Added {len(added)} player row(s) for {args.quiz.strip()} -> {results}")
    return 0


def run_quiz_score(args: argparse.Namespace) -> int:
    out = Path(args.out).expanduser()
    roster = roster_mod.load(Path(args.roster).expanduser())
    module = quiz_module_mod.score(
        quiz_module_mod.read_results(Path(args.results).expanduser()),
        roster,
        quiz_module_mod.parse_questions(args.questions, args.questions_for),
        _aliases(args.alias),
    )
    quiz_module_mod.write(module, out)
    active = len(roster.active)
    for quiz, count in module.scored.items():
        missing = [row[1] for row in module.rows if not row[module.headers.index(quiz)]]
        line = f"{quiz}: {count}/{active} scored"
        if missing:
            line += f"; no score for {', '.join(missing)}"
        print(line)
        if quiz in module.dropped:
            print(f"    dropped, left out: {', '.join(module.dropped[quiz])}")
        if quiz in module.unmatched:
            print(f"    NOTE not on the roster: {', '.join(module.unmatched[quiz])}")
    if module.unmatched:
        print(
            "NOTE: each unmatched nickname is a score left out. Map it with "
            "--alias NICK=STD_ID unless it belongs to another class."
        )
    print(f"Wrote {len(module.rows)} row(s) -> {out}")
    return 0


def run_export_fams_theory(args: argparse.Namespace) -> int:
    out = Path(args.out).expanduser()
    if args.quiz_scores:
        scores = fams_theory_mod.read_quiz_scores(Path(args.quiz_scores).expanduser())
    else:
        scores = fams_theory_mod.read_grades(Path(args.grades).expanduser())
    report = fams_theory_mod.export_theory(
        scores,
        out,
        roster=_roster(args.roster),
        template=Path(args.template).expanduser() if args.template else None,
        topic_code=args.topic_code,
        assessments=args.assessment,
    )
    _fams_report(report, out)
    return 0


def run_export_fams_practice(args: argparse.Namespace) -> int:
    out = Path(args.out).expanduser()
    report = fams_practice_mod.export_practice(
        Path(args.grades).expanduser(),
        out,
        roster=_roster(args.roster),
        template=Path(args.template).expanduser() if args.template else None,
        topic_code=args.topic_code,
        assessment=args.assessment,
        marker=args.marker,
        date=args.date,
        pass_mark=args.pass_mark,
        missing_comment=args.missing_comment,
        mark_label=args.mark_label,
    )
    _fams_report(report, out)
    return 0


def _fams_report(report, out: Path) -> None:
    """Both forms report alike: what the user must hear before importing."""
    for label, value in report.info.items():
        print(f"{label} {value}")
    for note in report.notes:
        print(f"NOTE: {note}")
    if report.left_out:
        print(f"Left out, not in the FAMS template: {', '.join(report.left_out)}")
    if report.zeroed:
        print(f"NOTE: no marks, written as 0: {', '.join(report.zeroed)}")
    for test, std_id in report.missed:
        print(f"    {test} missed, written as 0: {std_id}")
    if report.unmatched:
        print(f"NOTE: not on the roster, account kept as given: {', '.join(report.unmatched)}")
    print(f"Wrote {report.rows} row(s) -> {out}")


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

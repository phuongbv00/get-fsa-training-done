"""The grading pipeline, focused on the bugs the port set out to fix."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

import pytest

from fsa_trainer_skills.skills.assess.core.grading import (
    aggregate,
    ai_cheat,
    batches,
    plagiarism,
    preprocess,
)
from fsa_trainer_skills.skills.assess.core.grading import roster as roster_mod
from fsa_trainer_skills.skills.assess.core.grading.roster import std_id_from_folder

# --------------------------------------------------------------------------- #
# Roster
# --------------------------------------------------------------------------- #


def test_inactive_counts_as_dropped_everywhere(roster_csv):
    """The original scripts disagreed: three treated `inactive` as dropped and
    aggregate did not, so such a trainee was skipped at every stage and then
    silently reappeared in the grade CSV."""
    roster = roster_mod.load(roster_csv)
    assert roster.is_dropped("HieuLX14")
    assert roster.is_dropped("AnhPQ54")
    assert {t.std_id for t in roster.active} == {"PhuongBV3", "LinhTT127"}


def test_roster_lookup_is_case_insensitive(roster_csv):
    roster = roster_mod.load(roster_csv)
    assert roster.get("phuongbv3").std_id == "PhuongBV3"


def test_std_id_with_an_underscore_survives_the_folder_round_trip():
    """`name.split("_")[-1]` truncated any id containing an underscore, which
    then matched nothing and vanished from the results without a word."""
    folder = roster_mod.folder_name("JPL", "ASSIGNMENT", "Phuong_BV3")
    assert std_id_from_folder(folder, "JPL", "ASSIGNMENT") == "Phuong_BV3"


def test_std_id_from_folder_handles_the_ordinary_case():
    assert std_id_from_folder("JPL_ASSIGNMENT_PhuongBV3", "JPL", "ASSIGNMENT") == "PhuongBV3"


def test_roster_without_an_id_column_is_rejected(tmp_path):
    from fsa_trainer_skills.errors import UsageError

    bad = tmp_path / "r.csv"
    bad.write_text("No,Student,Name\n1,x,y\n", encoding="utf-8")
    with pytest.raises(UsageError, match="ID"):
        roster_mod.load(bad)


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #


def write_score(directory, std_id, tasks, **extra):
    directory.mkdir(parents=True, exist_ok=True)
    payload = {"std_id": std_id, "tasks": tasks, **extra}
    total = sum(t["score"] * t["weight"] / 100 for t in tasks)
    payload.setdefault("total", total)
    (directory / f"{std_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_aggregate_computes_the_weighted_total(tmp_path, roster_csv):
    scores = tmp_path / "_scores"
    write_score(
        scores,
        "PhuongBV3",
        [
            {"id": "T1", "name": "A", "max": 10, "weight": 60, "score": 8.0, "comment": "tốt"},
            {"id": "T2", "name": "B", "max": 10, "weight": 40, "score": 6.0, "comment": "ổn"},
        ],
    )
    result = aggregate.aggregate(scores_dir=scores, roster=roster_mod.load(roster_csv))
    assert result.rows[0][-1] == "7.2"
    assert result.rows[0][2] == "T1: tốt | T2: ổn"


def test_aggregate_excludes_dropped_and_inactive(tmp_path, roster_csv):
    scores = tmp_path / "_scores"
    tasks = [{"id": "T1", "name": "A", "max": 10, "weight": 100, "score": 9.0}]
    for std_id in ("PhuongBV3", "HieuLX14", "AnhPQ54"):
        write_score(scores, std_id, tasks)

    result = aggregate.aggregate(scores_dir=scores, roster=roster_mod.load(roster_csv))
    assert [row[0] for row in result.rows] == ["PhuongBV3"]
    assert set(result.skipped_dropped) == {"HieuLX14", "AnhPQ54"}


def test_aggregate_can_include_a_named_dropped_trainee(tmp_path, roster_csv):
    scores = tmp_path / "_scores"
    tasks = [{"id": "T1", "name": "A", "max": 10, "weight": 100, "score": 9.0}]
    for std_id in ("PhuongBV3", "HieuLX14"):
        write_score(scores, std_id, tasks)

    result = aggregate.aggregate(
        scores_dir=scores,
        roster=roster_mod.load(roster_csv),
        include_dropped=["HieuLX14"],
    )
    assert {row[0] for row in result.rows} == {"PhuongBV3", "HieuLX14"}


def test_aggregate_renders_legacy_reasons_without_their_amounts(tmp_path, roster_csv):
    """Score arithmetic is instructor-only and must never reach a learner."""
    scores = tmp_path / "_scores"
    write_score(
        scores,
        "PhuongBV3",
        [{"id": "T1", "name": "A", "max": 10, "weight": 100, "score": 8.0}],
        deductions=[{"amount": 1.5, "reason": "Nộp muộn"}],
    )
    result = aggregate.aggregate(scores_dir=scores, roster=roster_mod.load(roster_csv))
    comment = result.rows[0][2]
    assert "Nộp muộn" in comment
    assert "1.5" not in comment
    # The legacy deduction still affects the total, as it always did.
    assert result.rows[0][-1] == "6.5"


def test_aggregate_follows_roster_order(tmp_path, roster_csv):
    scores = tmp_path / "_scores"
    tasks = [{"id": "T1", "name": "A", "max": 10, "weight": 100, "score": 5.0}]
    for std_id in ("LinhTT127", "PhuongBV3"):
        write_score(scores, std_id, tasks)
    result = aggregate.aggregate(scores_dir=scores, roster=roster_mod.load(roster_csv))
    assert [row[0] for row in result.rows] == ["PhuongBV3", "LinhTT127"]


def test_aggregate_writes_a_bom_and_a_legend(tmp_path, roster_csv):
    scores = tmp_path / "_scores"
    write_score(
        scores, "PhuongBV3", [{"id": "T1", "name": "Schema", "max": 10, "weight": 100, "score": 7}]
    )
    result = aggregate.aggregate(scores_dir=scores, roster=roster_mod.load(roster_csv))
    out = tmp_path / "grades.csv"
    legend = aggregate.write(result, out)
    assert out.read_bytes().startswith(b"\xef\xbb\xbf")
    assert "T1 = T1  Schema" in legend.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Batching
# --------------------------------------------------------------------------- #


def test_batches_are_even_and_skip_already_scored(tmp_path, roster_csv):
    pre = tmp_path / "_preprocessed"
    for std_id in ("PhuongBV3", "LinhTT127"):
        (pre / roster_mod.folder_name("JPL", "ASSIGNMENT", std_id)).mkdir(parents=True)
    scores = tmp_path / "_scores"
    scores.mkdir()
    (scores / "PhuongBV3.json").write_text("{}", encoding="utf-8")

    plan = batches.plan(
        preprocessed=pre,
        scores=scores,
        roster=roster_mod.load(roster_csv),
        subject="JPL",
        submission_type="ASSIGNMENT",
        batch_count=2,
    )
    assert plan.total == 2
    assert plan.pending == 1
    assert plan.already_scored == 1
    assert plan.batches[0]["std_ids"] == ["LinhTT127"]


def test_batches_exclude_dropped_trainees(tmp_path, roster_csv):
    pre = tmp_path / "_preprocessed"
    for std_id in ("PhuongBV3", "HieuLX14"):
        (pre / roster_mod.folder_name("JPL", "ASSIGNMENT", std_id)).mkdir(parents=True)

    plan = batches.plan(
        preprocessed=pre,
        scores=tmp_path / "_scores",
        roster=roster_mod.load(roster_csv),
        subject="JPL",
        submission_type="ASSIGNMENT",
    )
    assert plan.dropped_std_ids == ["HieuLX14"]
    assert plan.total == 1


# --------------------------------------------------------------------------- #
# Similarity
# --------------------------------------------------------------------------- #


def test_fingerprints_are_reproducible_across_processes():
    """The original used the builtin `hash()`, which Python randomises per
    process, so two runs over the same submissions produced different numbers
    and a flagged pair could never be re-checked."""
    tokens = ["select", "id", "from", "users", "where", "active", "=", "1"] * 5
    assert plagiarism.fingerprints(tokens, 5, 4) == plagiarism.fingerprints(tokens, 5, 4)

    # A fixed expected value is the point: it only holds if the hash is stable
    # across processes and Python builds, which `hash()` is not.
    assert plagiarism.stable_hash("select id from users") == 128_528_833

    fresh = subprocess.run(
        [
            sys.executable,
            "-c",
            "import zlib; print(zlib.crc32(b'select id from users') & 0xFFFFFFFF)",
        ],
        capture_output=True,
        text=True,
    )
    assert int(fresh.stdout.strip()) == plagiarism.stable_hash("select id from users")


def test_identical_files_are_flagged(tmp_path):
    pre = tmp_path / "_preprocessed"
    source = "SELECT id, name FROM users WHERE active = 1 ORDER BY name;\n" * 12
    for std_id in ("PhuongBV3", "LinhTT127"):
        folder = pre / roster_mod.folder_name("JPL", "ASSIGNMENT", std_id)
        folder.mkdir(parents=True)
        (folder / "schema.sql").write_text(source, encoding="utf-8")

    report = plagiarism.run(preprocessed=pre, subject="JPL", submission_type="ASSIGNMENT")
    pairs = report.payload["flagged_pairs"]
    assert pairs and pairs[0]["similarity"] >= 0.9


def test_comments_and_strings_do_not_hide_a_copy(tmp_path):
    pre = tmp_path / "_preprocessed"
    body = "\n".join(f"const value{i} = compute({i}, total);" for i in range(30))
    variants = {
        "PhuongBV3": body,
        "LinhTT127": "// my own work\n" + body.replace("total", "total") + '\nconst s = "x";\n',
    }
    for std_id, text in variants.items():
        folder = pre / roster_mod.folder_name("JPL", "ASSIGNMENT", std_id)
        folder.mkdir(parents=True)
        (folder / "app.js").write_text(text, encoding="utf-8")

    report = plagiarism.run(preprocessed=pre, subject="JPL", submission_type="ASSIGNMENT")
    assert report.payload["flagged_pairs"]


def test_a_url_inside_a_string_does_not_swallow_the_line():
    """Comments used to be stripped before strings, so the `//` in a URL literal
    ate the rest of its line — and with it the code that followed."""
    tokens = plagiarism.tokenize('const base = "http://x.io"; const port = 8080;', "js")
    assert "port" in tokens


# --------------------------------------------------------------------------- #
# Preprocess
# --------------------------------------------------------------------------- #


def _preprocess(roster_csv, src):
    return preprocess.run(
        roster=roster_mod.load(roster_csv),
        src=src,
        out=src / "_preprocessed",
        subject="JPL",
        submission_type="ASSIGNMENT",
    )


def test_preprocess_keeps_a_loose_file_and_a_folder(roster_csv, tmp_path):
    """A document exam arrives as a bare PDF; it must not be reported as
    'did not submit' because it was never an archive."""
    src = tmp_path / "uploads"
    src.mkdir()
    (src / "PhuongBV3_jpl_assignment_01.pdf").write_bytes(b"%PDF-1.4")
    (src / "LinhTT127_jpl_assignment_01" / "nested").mkdir(parents=True)
    (src / "LinhTT127_jpl_assignment_01" / "nested" / "Main.java").write_text("class Main {}")

    outcome = _preprocess(roster_csv, src)

    out = src / "_preprocessed"
    assert {std_id for std_id, _, _ in outcome.created} == {"PhuongBV3", "LinhTT127"}
    assert outcome.missing == []
    assert (out / "JPL_ASSIGNMENT_PhuongBV3" / "PhuongBV3_jpl_assignment_01.pdf").is_file()
    # Redundant single-folder nesting is collapsed.
    assert (out / "JPL_ASSIGNMENT_LinhTT127" / "Main.java").is_file()


@pytest.mark.skipif(
    not any(map(shutil.which, ("ditto", "unzip", "bsdtar"))),
    reason="no zip extractor on this machine",
)
def test_a_failed_extraction_is_not_also_a_missing_submission(roster_csv, tmp_path):
    src = tmp_path / "uploads"
    src.mkdir()
    (src / "PhuongBV3_jpl_assignment_01.zip").write_bytes(b"not a zip at all")

    outcome = _preprocess(roster_csv, src)

    assert [name for name, _ in outcome.failures] == ["PhuongBV3_jpl_assignment_01.zip"]
    assert [std_id for std_id, _ in outcome.missing] == ["LinhTT127"]


# --------------------------------------------------------------------------- #
# AI-authorship signals
# --------------------------------------------------------------------------- #


def test_ai_cheat_counts_narration_and_pasted_characters(tmp_path):
    pre = tmp_path / "_preprocessed"
    folder = pre / "JPL_ASSIGNMENT_PhuongBV3"
    folder.mkdir(parents=True)
    (folder / "UserController.java").write_text(
        "// GET /users\n"
        '@GetMapping("/users")\n'
        "public List<User> listUsers() { return repo.findAll(); } // returns users → list\n",
        encoding="utf-8",
    )

    report = ai_cheat.run(preprocessed=[pre], subject="JPL", submission_type="ASSIGNMENT")
    metrics = report.payload["students"]["PhuongBV3"]

    assert metrics["endpoint_narration"] == 1
    assert metrics["non_keyboard_by_kind"] == {"right arrow": 1}
    assert "INSTRUCTOR ONLY" in report.text

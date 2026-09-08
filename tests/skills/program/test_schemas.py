"""CSV schemas, and the column tails that must be derived rather than assumed."""

from __future__ import annotations

import pytest

from fsa_trainer_skills.errors import UsageError
from fsa_trainer_skills.skills.program.core import csvio, schemas


def test_the_week_and_day_tails_are_counted_from_the_header():
    """`W1..W14` and `D1..D96` were constants in the reference pipeline.

    They are properties of how long a programme runs, so they come from the
    file rather than from the tool.
    """
    headers = ["Semester", "Topics", "Module", *[f"W{n}" for n in range(1, 15)]]
    assert schemas.derive_index_tail(headers, "W") == 14

    short = ["Semester", "Topics", "Module", "W1", "W2"]
    assert schemas.derive_index_tail(short, "W") == 2


def test_a_gap_in_the_tail_is_an_error_not_a_count():
    """`W1,W3` means a column was deleted by hand. Reading it as two weeks puts
    every later assertion one column out, silently."""
    with pytest.raises(schemas.SchemaError, match="in order"):
        schemas.derive_index_tail(["Semester", "W1", "W3"], "W")


def test_an_out_of_order_tail_is_an_error():
    with pytest.raises(schemas.SchemaError, match="in order"):
        schemas.derive_index_tail(["Semester", "W2", "W1"], "W")


def test_a_missing_tail_is_an_error():
    with pytest.raises(schemas.SchemaError, match="no WN columns"):
        schemas.derive_index_tail(["Semester", "Topics"], "W")


def test_expected_headers_compose_the_fixed_prefix_with_the_derived_tail():
    assert schemas.expected_headers(schemas.MASTER_SCHEDULE, count=2) == [
        "Semester",
        "Topics",
        "Module",
        "W1",
        "W2",
    ]
    assert schemas.expected_headers(schemas.OST_MAPPING, modules=("A", "B"))[-2:] == ["A", "B"]


def test_session_means_different_things_in_the_two_schedules():
    """Same column name, different type — so they share no cell validator.

    In a topic's ScheduleDetail `Session` is a number; in the programme's
    DetailedSchedule it is the literal string "Technical half-day".
    """
    assert "Session" in schemas.DETAILED_SCHEDULE.fixed
    assert "Session" in schemas.SCHEDULE_DETAIL.fixed
    assert schemas.DETAILED_SCHEDULE is not schemas.SCHEDULE_DETAIL


# --- CSV reading ----------------------------------------------------------


def test_a_byte_order_mark_does_not_corrupt_the_first_header(tmp_path):
    """Files round-tripped through Excel carry a BOM, and a BOM on "Semester"
    makes it match nothing."""
    path = tmp_path / "m.csv"
    path.write_bytes("Semester,Topics\n1,x\n".encode("utf-8-sig"))

    table = csvio.read_table(path)

    assert table.headers == ["Semester", "Topics"]
    assert table.rows == [{"Semester": "1", "Topics": "x"}]


def test_blank_cells_read_as_empty_strings(tmp_path):
    """ "No hours that day" and "zero hours" are different, and the CSV writes
    the first as an empty cell."""
    path = tmp_path / "d.csv"
    path.write_text("Module,D1,D2\nA,4,\n", encoding="utf-8")

    assert csvio.read_table(path).rows == [{"Module": "A", "D1": "4", "D2": ""}]


def test_short_rows_are_padded_rather_than_losing_columns(tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("Module,D1,D2\nA,4\n", encoding="utf-8")

    assert csvio.read_table(path).rows[0]["D2"] == ""


def test_blank_lines_are_skipped(tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("Module,D1\nA,4\n\n,\n", encoding="utf-8")

    assert len(csvio.read_table(path).rows) == 1


def test_a_missing_file_is_a_usage_error(tmp_path):
    with pytest.raises(UsageError, match="CSV not found"):
        csvio.read_table(tmp_path / "nope.csv")

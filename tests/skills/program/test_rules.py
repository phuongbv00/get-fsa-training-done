"""One case per rule.

A rule that never fires is documentation, not a check — and `references/rules.md`
is generated from the same table the model reads, so an unenforced rule teaches
the model a constraint nothing holds it to. Each case makes one targeted edit to
the clean programme and asserts that rule fires.

Some edits necessarily trip more than one rule: changing a total breaks both the
sum and the length of a training day derived from it. The assertion is that the
named rule is *among* those fired, not that it is alone.
"""

from __future__ import annotations

import pytest

from fsa_trainer_skills.skills.program.core import rules

CURRICULUM = "curriculum/AA_FR_TT_DEMO_TrainingProgramCurriculum.md"
MASTER = "curriculum/AA_FR_TT_DEMO_MasterSchedule.csv"
DETAILED = "curriculum/AA_FR_TT_DEMO_DetailedSchedule.csv"
TOPIC_LIST = "curriculum/AA_FR_TT_DEMO_TopicList.csv"
OST = "curriculum/AA_FR_TT_DEMO_OSTModuleMapping.csv"
DBF = "curriculum/syllabi/AA_FR_TT_DBF_Syllabus.md"
DBF_PLAN = "curriculum/syllabi/AA_FR_TT_DBF_ScheduleDetail.csv"
FND = "curriculum/syllabi/AA_FR_TT_FND_Syllabus.md"


def test_the_shipped_programme_is_clean(fired, mini):
    """Everything else here is a deviation from this baseline."""
    assert fired(mini) == set()


# --- Programme level ------------------------------------------------------


def test_p01_module_hours_must_reconcile_to_the_total(fired, mini, edit):
    edit(mini, CURRICULUM, "**20**", "**24**")
    assert "PRG-P01" in fired(mini)


def test_p02_a_training_day_must_be_whole_minutes(fired, mini, edit):
    edit(mini, CURRICULUM, "| **TOTAL** | | **20** | **5** |", "| **TOTAL** | | **20** | **7** |")
    assert "PRG-P02" in fired(mini)


def test_p03_a_renamed_column_is_caught(fired, mini, edit):
    edit(mini, MASTER, "Semester,Topics,Module,W1", "Semester,Topic,Module,W1")
    assert "PRG-P03" in fired(mini)


def test_p03_a_missing_file_is_caught(fired, mini):
    (mini / TOPIC_LIST).unlink()
    assert "PRG-P03" in fired(mini)


def test_p04_a_missing_module_row_is_caught(fired, mini, edit):
    edit(mini, TOPIC_LIST, "AA_FR_TT_DBF,Databases,Databases,Common\n", "")
    assert "PRG-P04" in fired(mini)


def test_p05_a_module_with_no_assessment_week_is_caught(fired, mini, edit):
    edit(mini, MASTER, "AA_FR_TT_FND,Mark", "AA_FR_TT_FND,")
    assert "PRG-P05" in fired(mini)


def test_p05_a_module_assessed_twice_is_caught(fired, mini, edit):
    edit(mini, MASTER, "Semester,Topics,Module,W1", "Semester,Topics,Module,W1,W2")
    edit(mini, MASTER, "AA_FR_TT_FND,Mark", "AA_FR_TT_FND,Mark,Mark")
    edit(mini, MASTER, "AA_FR_TT_DBF,Mark", "AA_FR_TT_DBF,Mark,")
    assert "PRG-P05" in fired(mini)


def test_p06_day_cells_must_equal_the_declared_hours(fired, mini, edit):
    edit(
        mini,
        DETAILED,
        "AA_FR_TT_FND,8,Technical half-day,4,4",
        "AA_FR_TT_FND,8,Technical half-day,4,2",
    )
    assert "PRG-P06" in fired(mini)


def test_p07_scheduled_hours_must_equal_the_programme_total(fired, mini, edit):
    edit(
        mini,
        DETAILED,
        "AA_FR_TT_DBF,12,Technical half-day,,,4,4,4",
        "AA_FR_TT_DBF,8,Technical half-day,,,4,4,",
    )
    assert "PRG-P07" in fired(mini)


def test_p08_the_number_of_teaching_days_must_match(fired, mini, edit):
    edit(
        mini,
        DETAILED,
        "AA_FR_TT_DBF,12,Technical half-day,,,4,4,4",
        "AA_FR_TT_DBF,12,Technical half-day,,,6,6,",
    )
    assert "PRG-P08" in fired(mini)


def test_p09_weekend_columns_must_be_blank(fired, mini):
    """Which columns are weekends depends on the weekday the programme starts,
    so this is an input rather than a constant."""
    assert "PRG-P09" in fired(mini, "--first-weekday", "sun")


def test_p10_week_and_day_counts_should_agree(fired, mini, edit):
    edit(mini, MASTER, "Semester,Topics,Module,W1", "Semester,Topics,Module,W1,W2")
    edit(mini, MASTER, "AA_FR_TT_FND,Mark", "AA_FR_TT_FND,Mark,")
    edit(mini, MASTER, "AA_FR_TT_DBF,Mark", "AA_FR_TT_DBF,Mark,")
    assert "PRG-P10" in fired(mini)


def test_p11_an_unmapped_outcome_standard_is_caught(fired, mini, edit):
    edit(mini, OST, "Guided practice,x,", "Guided practice,,")
    assert "PRG-P11" in fired(mini)


def test_p12_a_topic_name_that_drifts_from_the_module_table(fired, mini, edit):
    edit(mini, TOPIC_LIST, "AA_FR_TT_DBF,Databases", "AA_FR_TT_DBF,Data Bases")
    assert "PRG-P12" in fired(mini)


# --- Topic level ----------------------------------------------------------


def test_s01_the_session_plan_header_is_fixed(fired, mini, edit):
    edit(mini, DBF_PLAN, "Duration (mins)", "Duration (min)")
    assert "PRG-S01" in fired(mini)


def test_s02_identity_must_agree_across_the_three_places_it_is_stated(fired, mini, edit):
    edit(
        mini,
        DBF,
        "| 3 | **Topic Code** | `AA_FR_TT_DBF` |",
        "| 3 | **Topic Code** | `AA_FR_TT_XXX` |",
    )
    assert "PRG-S02" in fired(mini)


def test_s03_an_unknown_delivery_type_is_caught(fired, mini, edit):
    edit(mini, DBF_PLAN, "Concept/Lecture,60", "Lecture,60")
    assert "PRG-S03" in fired(mini)


def test_s03_a_non_blended_training_format_is_caught(fired, mini, edit):
    edit(mini, DBF_PLAN, ",Blended,", ",Online,")
    assert "PRG-S03" in fired(mini)


def test_s04_a_non_numeric_duration_is_caught(fired, mini, edit):
    edit(mini, DBF_PLAN, "Concept/Lecture,60", "Concept/Lecture,sixty")
    assert "PRG-S04" in fired(mini)


def test_s05_minutes_must_equal_days_times_a_training_day(fired, mini, edit):
    edit(mini, DBF, "**Days:** 3", "**Days:** 4")
    assert "PRG-S05" in fired(mini)


def test_s06_no_session_may_outrun_a_training_day(fired, mini, edit):
    edit(mini, DBF_PLAN, "Concept/Lecture,60", "Concept/Lecture,90")
    assert "PRG-S06" in fired(mini)


def test_s07_a_session_belongs_to_one_chapter(fired, mini, edit):
    edit(mini, DBF_PLAN, "1,Relational Modelling,1,Quiz 1", "2,Querying and Assessment,1,Quiz 1")
    assert "PRG-S07" in fired(mini)


def test_s08_a_chapter_spanning_too_many_sessions_warns(fired, mini):
    """Advisory: a capstone groups a chapter by sprint on purpose."""
    assert "PRG-S08" in fired(mini, "--max-sessions-per-chapter", "1")


def test_s09_a_time_allocation_share_that_drifts_is_caught(fired, mini, edit):
    edit(mini, DBF, "| Concept/Lecture | 20.83% |", "| Concept/Lecture | 25.00% |")
    assert "PRG-S09" in fired(mini)


def test_s10_weights_must_sum_to_one_hundred(fired, mini, edit):
    edit(mini, DBF, "| Quiz | 2 | 10% |", "| Quiz | 2 | 15% |")
    assert "PRG-S10" in fired(mini)


def test_s11_pass_criteria_must_not_carry_a_weight(fired, mini, edit):
    edit(mini, DBF, "| **Pass Criteria** | **6** | |", "| **Pass Criteria** | **6** | 5% |")
    assert "PRG-S11" in fired(mini)


def test_s11_the_pass_mark_is_an_input(fired, mini):
    assert "PRG-S11" in fired(mini, "--pass-mark", "7")


def test_s12_a_count_that_the_session_plan_does_not_deliver(fired, mini, edit):
    edit(mini, DBF, "| Quiz | 2 | 10% |", "| Quiz | 3 | 10% |")
    assert "PRG-S12" in fired(mini)


def test_s13_quizzes_clustered_in_one_chapter_warn(fired, mini, edit):
    edit(mini, DBF_PLAN, "2,Querying and Assessment,3,Quiz 2", "1,Relational Modelling,3,Quiz 2")
    assert "PRG-S13" in fired(mini)


def test_s14_an_item_with_no_row_pattern_warns(fired, mini, edit):
    edit(
        mini,
        DBF,
        "| Quiz | 2 | 10% |",
        "| Portfolio | 1 | 0% | Unknown to the matcher |\n| Quiz | 2 | 10% |",
    )
    assert "PRG-S14" in fired(mini)


def test_s15_a_section_the_workbook_cannot_hold_is_caught(fired, mini, edit):
    edit(mini, DBF, "### 7. Topic Outline", "### Duration\n\nThree days.\n\n### 7. Topic Outline")
    assert "PRG-S15" in fired(mini)


def test_s16_more_than_one_change_record_is_caught(fired, mini, edit):
    edit(
        mini,
        DBF,
        "| 21/08/2026 | Create new | A | Create syllabus | 2026.4 |",
        "| 21/08/2026 | Create new | A | Create syllabus | 2026.4 |\n"
        "| 22/08/2026 | Tweak | M | Fix a typo | 2026.5 |",
    )
    assert "PRG-S16" in fired(mini)


def test_s17_a_creator_mismatch_warns(fired, mini):
    """Advisory: the creator is an input, and a programme may be authored by
    someone other than whoever runs the check."""
    assert "PRG-S17" in fired(mini, "--creator", "Someone Else")


def test_s18_a_syllabus_with_no_objectives_is_caught(fired, mini, edit):
    edit(mini, DBF, "| Core practice | DBF-K1 |", "| | |")
    edit(mini, DBF, "| Applied work | DBF-K2 |", "| | |")
    assert "PRG-S18" in fired(mini)


def test_s19_a_session_citing_an_undefined_objective_warns(fired, mini, edit):
    edit(mini, DBF_PLAN, "DBF-K1,Concept/Lecture,60", "DBF-K9,Concept/Lecture,60")
    assert "PRG-S19" in fired(mini)


# --- Cross-links ----------------------------------------------------------


def test_x01_a_module_with_no_syllabus_is_caught(fired, mini):
    (mini / DBF).unlink()
    assert "PRG-X01" in fired(mini)


def test_x01_a_syllabus_with_no_module_is_caught(fired, mini, edit):
    edit(
        mini,
        CURRICULUM,
        "| 2 | Databases | `AA_FR_TT_DBF` | 12 | 3 | Relational modelling and SQL. |\n",
        "",
    )
    edit(mini, CURRICULUM, "**20**", "**8**")
    edit(mini, CURRICULUM, "| **TOTAL** | | **8** | **5** |", "| **TOTAL** | | **8** | **2** |")
    assert "PRG-X01" in fired(mini)


def test_x02_the_syllabus_days_must_sum_to_the_programme(fired, mini, edit):
    edit(mini, CURRICULUM, "| **TOTAL** | | **20** | **5** |", "| **TOTAL** | | **20** | **4** |")
    assert "PRG-X02" in fired(mini)


def test_x03_a_module_length_that_disagrees_with_its_syllabus(fired, mini, edit):
    edit(mini, CURRICULUM, "| `AA_FR_TT_DBF` | 12 | 3 |", "| `AA_FR_TT_DBF` | 12 | 2 |")
    assert "PRG-X03" in fired(mini)


def test_x04_a_topic_code_outside_the_programme_prefix_warns(fired, mini, edit):
    edit(mini, CURRICULUM, "`AA_FR_TT_DBF`", "`ZZ_FR_TT_DBF`")
    assert "PRG-X04" in fired(mini)


def test_x05_an_audience_that_contradicts_the_level_warns(fired, mini, edit):
    edit(
        mini,
        DBF,
        "| 5 | **Training Audience** | Fresher — TT track |",
        "| 5 | **Training Audience** | Senior engineers |",
    )
    assert "PRG-X05" in fired(mini)


# --- Coverage -------------------------------------------------------------


def test_every_rule_has_a_case_here():
    """The registry and this file must not drift apart."""
    source = __import__("pathlib").Path(__file__).read_text(encoding="utf-8")
    uncovered = [rule.id for rule in rules.RULES if rule.id not in source]
    assert uncovered == []


def test_no_duplicate_rule_ids():
    ids = [rule.id for rule in rules.RULES]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("rule", rules.RULES, ids=lambda r: r.id)
def test_every_rule_is_documented(rule):
    assert rule.title and rule.rationale
    assert rule.severity in {"error", "warning"}
    assert rule.scope in {"program", "topic", "cross"}

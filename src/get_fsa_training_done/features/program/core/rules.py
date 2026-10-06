"""The rulebook: what "this programme reconciles" means, stated once.

Every rule has an id, and every finding carries it, so a failure is a lookup
rather than a paragraph to interpret. `references/rules.md` is generated from
this table — if the prose said a session may run 240 minutes while the checker
allowed 300, the model would calibrate to a number nothing enforces.

Rule bodies live in `checks/`, registered against these ids. A rule declared
here with no body, or a body citing an id not declared here, fails a test — the
two halves cannot drift apart.

Ids are grouped by what they read: `PRG-P*` the programme-level files, `PRG-S*`
one topic's syllabus and session plan, `PRG-X*` the links between them.
"""

from __future__ import annotations

from dataclasses import dataclass

from get_fsa_training_done.features.common.findings import ERROR, WARNING


@dataclass(frozen=True)
class Rule:
    id: str
    scope: str  # "program" | "topic" | "cross"
    severity: str
    title: str
    rationale: str


RULES: tuple[Rule, ...] = (
    # --- Programme level ---------------------------------------------------
    Rule(
        "PRG-P01",
        "program",
        ERROR,
        "Module hours and days reconcile to the TOTAL row",
        "The TOTAL row is what every other figure is derived from — the length "
        "of a training day comes from it. A total that does not match its own "
        "rows silently rescales the whole programme.",
    ),
    Rule(
        "PRG-P02",
        "program",
        ERROR,
        "A training day is a whole number of minutes",
        "Hours divided by days gives the length of a training day. When that is "
        "not a whole number the two totals disagree about what a day is, and "
        "every per-topic minute check inherits the error.",
    ),
    Rule(
        "PRG-P03",
        "program",
        ERROR,
        "Each programme CSV has the header its schema requires",
        "The headers become the workbook's columns. A renamed or missing one is "
        "not caught at export — it writes the wrong column.",
    ),
    Rule(
        "PRG-P04",
        "program",
        ERROR,
        "Each programme CSV has exactly one row per module, in module order",
        "The tables are joined by position as well as by code, so a missing or "
        "reordered row misaligns every mapping downstream.",
    ),
    Rule(
        "PRG-P05",
        "program",
        ERROR,
        "Every MasterSchedule row marks exactly one assessment week",
        "The mark is the assessment week. None means the module is never "
        "assessed; two means the schedule contradicts itself.",
    ),
    Rule(
        "PRG-P06",
        "program",
        ERROR,
        "Each DetailedSchedule row's day cells sum to its Drt (h)",
        "The row states its own hours and then spends them across days. When "
        "the two disagree the calendar is not the programme it claims to be.",
    ),
    Rule(
        "PRG-P07",
        "program",
        ERROR,
        "DetailedSchedule hours sum to the programme total",
        "Per-row correctness does not imply the whole calendar adds up.",
    ),
    Rule(
        "PRG-P08",
        "program",
        ERROR,
        "The number of days actually scheduled equals the programme's day total",
        "Hours can reconcile while the work is spread over the wrong number of "
        "days, which is what the delivery calendar is for.",
    ),
    Rule(
        "PRG-P09",
        "program",
        ERROR,
        "Weekend columns are empty",
        "The day grid is calendar days, not working days, so weekends are "
        "positions that must stay blank. Which columns those are depends on the "
        "weekday the programme starts.",
    ),
    Rule(
        "PRG-P10",
        "program",
        WARNING,
        "The week count matches the day count",
        "Weeks and days are two views of one calendar. A mismatch is usually a "
        "column added by hand, and it is a warning because a programme may "
        "legitimately reserve trailing weeks.",
    ),
    Rule(
        "PRG-P11",
        "program",
        ERROR,
        "Every outcome standard maps to at least one module",
        "An unmapped outcome is one the programme claims to deliver and never teaches.",
    ),
    Rule(
        "PRG-P12",
        "program",
        ERROR,
        "TopicList names match the module table",
        "The topic list is the module table in another shape; a divergence "
        "means one of them was edited alone.",
    ),
    # --- Topic level -------------------------------------------------------
    Rule(
        "PRG-S01",
        "topic",
        ERROR,
        "The session plan has the fixed ScheduleDetail header",
        "The nine columns are written straight into the workbook, by position.",
    ),
    Rule(
        "PRG-S02",
        "topic",
        ERROR,
        "The syllabus code matches its filename and its Topic Code field",
        "Three statements of one identity; when they disagree the pair cannot "
        "be matched to its module.",
    ),
    Rule(
        "PRG-S03",
        "topic",
        ERROR,
        "Every row uses a known delivery type and the Blended training format",
        "Both are closed vocabularies the workbook validates against.",
    ),
    Rule(
        "PRG-S04",
        "topic",
        ERROR,
        "Session and duration are numeric",
        "Everything else about a topic is a sum over these two columns.",
    ),
    Rule(
        "PRG-S05",
        "topic",
        ERROR,
        "Total minutes equal the declared days times the length of a training day",
        "This is the check that ties a syllabus to the programme's calendar.",
    ),
    Rule(
        "PRG-S06",
        "topic",
        ERROR,
        "No session runs longer than a training day",
        "A session is a day's teaching. One that overruns cannot be delivered "
        "as scheduled, however well the totals add up.",
    ),
    Rule(
        "PRG-S07",
        "topic",
        ERROR,
        "A session belongs to exactly one chapter",
        "The workbook merges the chapter column across a session's rows, so a "
        "session split across chapters renders as a merge over the wrong span.",
    ),
    Rule(
        "PRG-S08",
        "topic",
        WARNING,
        "A chapter spans no more than the allowed number of sessions",
        "A chapter stretched over many sessions usually wants splitting — but a "
        "capstone deliberately groups by sprint, so this is advisory.",
    ),
    Rule(
        "PRG-S09",
        "topic",
        ERROR,
        "Each Time Allocation share matches the session plan",
        "The shares are a summary of the plan. Typed by hand they drift from it, "
        "and the workbook shows the typed figure.",
    ),
    Rule(
        "PRG-S10",
        "topic",
        ERROR,
        "Assessment weights sum to 100",
        "The weights are the topic's mark scheme.",
    ),
    Rule(
        "PRG-S11",
        "topic",
        ERROR,
        "Pass Criteria is the last row, with a count and no weight",
        "It is a threshold, not a component; a weight there would double-count.",
    ),
    Rule(
        "PRG-S12",
        "topic",
        ERROR,
        "Each assessment item's count matches the session plan",
        "The scheme promises a number of quizzes or reviews; the plan is where "
        "they actually happen.",
    ),
    Rule(
        "PRG-S13",
        "topic",
        WARNING,
        "Quizzes are spread across more than one chapter",
        "Quizzes clustered in one chapter sample a fraction of the topic.",
    ),
    Rule(
        "PRG-S14",
        "topic",
        WARNING,
        "An assessment item has a row pattern that can count it",
        "An item nothing can match is never checked against the plan, so its "
        "count is taken on trust.",
    ),
    Rule(
        "PRG-S15",
        "topic",
        ERROR,
        "The syllabus carries no section the export contract has no cell for",
        "An unsupported section is dropped silently on export, so the delivered "
        "workbook says less than the source document.",
    ),
    Rule(
        "PRG-S16",
        "topic",
        ERROR,
        "There is exactly one change record, and it is an addition",
        "A new syllabus has one 'Added' record; more means edits were made "
        "without versioning them.",
    ),
    Rule(
        "PRG-S17",
        "topic",
        WARNING,
        "Authorship matches the declared creator",
        "Advisory because the creator is an input, and a programme may be "
        "authored by someone other than the person running the check.",
    ),
    Rule(
        "PRG-S18",
        "topic",
        ERROR,
        "Course objectives and the topic outline are present",
        "They are the syllabus's substance, and the workbook has cells for both.",
    ),
    Rule(
        "PRG-S19",
        "topic",
        WARNING,
        "Every objective code a session cites is defined in the syllabus",
        "A session claiming an objective the topic does not list is either a "
        "typo or a missing objective.",
    ),
    # --- Cross-links -------------------------------------------------------
    Rule(
        "PRG-X01",
        "cross",
        ERROR,
        "Every module has a syllabus pair, and every pair has a module",
        "Checked both ways: a missing syllabus is an undelivered module, and a "
        "stray one is a topic nobody scheduled.",
    ),
    Rule(
        "PRG-X02",
        "cross",
        ERROR,
        "The syllabus day counts sum to the programme's day total",
        "Each topic can agree with itself while the programme over-commits.",
    ),
    Rule(
        "PRG-X03",
        "cross",
        ERROR,
        "Each module's declared days match its syllabus",
        "The module table and the syllabus both state a length.",
    ),
    Rule(
        "PRG-X04",
        "cross",
        WARNING,
        "Topic codes share the programme's site, level and track",
        "The prefix is what identifies a topic as part of this programme.",
    ),
    Rule(
        "PRG-X05",
        "cross",
        WARNING,
        "The training audience matches the level the code claims",
        "A code says FR while the audience says something else means one of "
        "them was copied from another programme.",
    ),
)

BY_ID = {rule.id: rule for rule in RULES}


def get(rule_id: str) -> Rule:
    try:
        return BY_ID[rule_id]
    except KeyError:
        raise KeyError(f"unknown rule id {rule_id!r}") from None


__all__ = ["BY_ID", "RULES", "Rule", "get"]

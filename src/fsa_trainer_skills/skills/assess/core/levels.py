"""Level calibration — the single source of truth for how hard an assessment is.

A level is *who the assessment is for*, and it is the one input that changes
almost every default: the Bloom mix, the difficulty mix, how long the work
takes, how much of the specification is handed over versus discovered, and how
strict the rubric is about justification.

Two axes, because they answer different questions:

* `UP_SKILL` — same technology stack, greater depth. The candidate already
  works in this stack; the assessment probes how far.
* `RE_SKILL` — an experienced engineer arriving from a *different* stack.
  Transferable reasoning is high but stack-specific recall is not assumed, so
  these assessments lean on migration, integration, and modernisation framing
  and never reward knowing an idiom by heart.

`CPL` and `FR` have no bands. `UP_SKILL` and `RE_SKILL` split into
`junior`/`mid`/`senior`, giving eight calibration targets in all.

The numbers here are defaults, not rules — Step 0 always lets the user override
them, and `verify` reports drift from the level default as a warning rather
than an error.
"""

from __future__ import annotations

from dataclasses import dataclass, field

BLOOM_ORDER = ("Remember", "Understand", "Apply", "Analyze")
DIFFICULTY_ORDER = ("Easy", "Medium", "Hard")
BANDS = ("junior", "mid", "senior")


@dataclass(frozen=True)
class Level:
    key: str
    band: str
    audience: str
    #: Percentages over BLOOM_ORDER; sums to 100.
    bloom: dict[str, int]
    #: Percentages over DIFFICULTY_ORDER; sums to 100.
    difficulty: dict[str, int]
    #: Seconds per question by difficulty, for question-set assessments.
    time_map: dict[str, str]
    #: Multiplier applied to a baseline duration when proposing one.
    duration_factor: float
    #: Suggested task count for long-form work.
    task_range: tuple[int, int]
    scope: str
    rubric_posture: str
    #: When False, a brief should state the outcome and let the candidate choose
    #: the mechanism. When True, naming the mechanism is fine because the
    #: mechanism itself is the learning objective.
    may_name_mechanism: bool
    notes: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def id(self) -> str:
        return f"{self.key}:{self.band}" if self.band else self.key

    @property
    def display(self) -> str:
        return f"{self.key} ({self.band})" if self.band else self.key


def _level(**kwargs) -> Level:
    level = Level(**kwargs)
    for name, table, order in (
        ("bloom", level.bloom, BLOOM_ORDER),
        ("difficulty", level.difficulty, DIFFICULTY_ORDER),
    ):
        total = sum(table.values())
        if total != 100:
            raise ValueError(f"{level.id}: {name} percentages sum to {total}, not 100")
        if set(table) - set(order):
            raise ValueError(f"{level.id}: unknown {name} key")
    return level


QUIZ_TIME_MAP = {"Easy": "5", "Medium": "10", "Hard": "20"}
EXAM_TIME_MAP = {"Easy": "30", "Medium": "45", "Hard": "75"}

LEVELS: tuple[Level, ...] = (
    _level(
        key="CPL",
        band="",
        audience="intern",
        bloom={"Remember": 30, "Understand": 40, "Apply": 30, "Analyze": 0},
        difficulty={"Easy": 50, "Medium": 35, "Hard": 15},
        time_map=QUIZ_TIME_MAP,
        duration_factor=0.75,
        task_range=(3, 4),
        scope="guided; the specification is given in full and there is one intended path",
        rubric_posture=(
            "generous partial credit; reward a correct partial solution over a broken complete one"
        ),
        may_name_mechanism=True,
        notes=(
            "Assess whether the trainee can follow a specification accurately. "
            "Do not test design judgement they have not been taught yet."
        ),
        aliases=("intern", "internship"),
    ),
    _level(
        key="FR",
        band="",
        audience="fresher",
        bloom={"Remember": 15, "Understand": 30, "Apply": 40, "Analyze": 15},
        difficulty={"Easy": 30, "Medium": 45, "Hard": 25},
        time_map=QUIZ_TIME_MAP,
        duration_factor=1.0,
        task_range=(4, 6),
        scope="spec-driven, with a few decisions left open",
        rubric_posture="balanced; correctness first, then the named mechanisms",
        may_name_mechanism=True,
        notes=(
            "The programme baseline. Name a mechanism when the mechanism is the "
            "learning objective; otherwise state the outcome."
        ),
        aliases=("fresher",),
    ),
    _level(
        key="UP_SKILL",
        band="junior",
        audience="junior moving toward mid",
        bloom={"Remember": 5, "Understand": 25, "Apply": 45, "Analyze": 25},
        difficulty={"Easy": 20, "Medium": 45, "Hard": 35},
        time_map=EXAM_TIME_MAP,
        duration_factor=1.0,
        task_range=(4, 6),
        scope="open-ended; the candidate makes the design decisions",
        rubric_posture="stricter caps; a missing foundation caps the whole task",
        may_name_mechanism=False,
    ),
    _level(
        key="UP_SKILL",
        band="mid",
        audience="mid-level",
        bloom={"Remember": 0, "Understand": 15, "Apply": 45, "Analyze": 40},
        difficulty={"Easy": 15, "Medium": 40, "Hard": 45},
        time_map=EXAM_TIME_MAP,
        duration_factor=1.25,
        task_range=(4, 6),
        scope="deliberately ambiguous requirements; scoping is part of the assessment",
        rubric_posture="trade-offs must be justified, not just made",
        may_name_mechanism=False,
    ),
    _level(
        key="UP_SKILL",
        band="senior",
        audience="senior",
        bloom={"Remember": 0, "Understand": 10, "Apply": 40, "Analyze": 50},
        difficulty={"Easy": 10, "Medium": 35, "Hard": 55},
        time_map=EXAM_TIME_MAP,
        duration_factor=1.5,
        task_range=(3, 5),
        scope="architecture and failure modes; correctness under load and partial failure",
        rubric_posture=(
            "evidence of judgement required; a working solution with no reasoning caps out"
        ),
        may_name_mechanism=False,
    ),
    _level(
        key="RE_SKILL",
        band="junior",
        audience="junior engineer new to this stack",
        bloom={"Remember": 10, "Understand": 30, "Apply": 45, "Analyze": 15},
        difficulty={"Easy": 25, "Medium": 45, "Hard": 30},
        time_map=EXAM_TIME_MAP,
        duration_factor=1.1,
        task_range=(4, 6),
        scope="porting a familiar pattern into the new stack",
        rubric_posture="never penalise unfamiliarity with an idiom; grade the reasoning",
        may_name_mechanism=True,
        notes="Name the stack-specific mechanism — it is new to them by definition.",
    ),
    _level(
        key="RE_SKILL",
        band="mid",
        audience="mid-level engineer new to this stack",
        bloom={"Remember": 5, "Understand": 20, "Apply": 45, "Analyze": 30},
        difficulty={"Easy": 20, "Medium": 40, "Hard": 40},
        time_map=EXAM_TIME_MAP,
        duration_factor=1.25,
        task_range=(4, 6),
        scope="cross-stack integration; the two stacks have to talk to each other",
        rubric_posture="transferable reasoning carries the marks, not stack trivia",
        may_name_mechanism=True,
    ),
    _level(
        key="RE_SKILL",
        band="senior",
        audience="senior engineer new to this stack",
        bloom={"Remember": 0, "Understand": 15, "Apply": 40, "Analyze": 45},
        difficulty={"Easy": 15, "Medium": 35, "Hard": 50},
        time_map=EXAM_TIME_MAP,
        duration_factor=1.5,
        task_range=(3, 5),
        scope="legacy modernisation and cross-cutting concerns",
        rubric_posture="migration strategy and risk assessment weigh as much as the code",
        may_name_mechanism=True,
    ),
)

LEVEL_KEYS = tuple(dict.fromkeys(level.key for level in LEVELS))
BANDED_KEYS = tuple(dict.fromkeys(level.key for level in LEVELS if level.band))


class UnknownLevel(ValueError):
    pass


def _normalise(value: str) -> str:
    return value.strip().upper().replace("-", "_").replace(" ", "_")


def resolve(key: str, band: str | None = None) -> Level:
    """Look up a level, tolerating aliases and a missing or surplus band."""
    normalised = _normalise(key)
    for level in LEVELS:
        if normalised in {_normalise(alias) for alias in level.aliases}:
            normalised = level.key
            break

    candidates = [level for level in LEVELS if level.key == normalised]
    if not candidates:
        raise UnknownLevel(f"unknown level {key!r}; choose from {', '.join(LEVEL_KEYS)}")

    if len(candidates) == 1:
        if band:
            raise UnknownLevel(f"{candidates[0].key} has no bands; drop --band")
        return candidates[0]

    if not band:
        raise UnknownLevel(f"{normalised} needs a band; choose from {', '.join(BANDS)}")
    wanted = band.strip().lower()
    for level in candidates:
        if level.band == wanted:
            return level
    raise UnknownLevel(f"unknown band {band!r} for {normalised}; choose from {', '.join(BANDS)}")


def time_map_for(level: Level, assessment_type: str) -> dict[str, str]:
    """Per-question seconds, which depend on the format as well as the level."""
    if assessment_type == "quiz":
        return dict(QUIZ_TIME_MAP)
    return dict(level.time_map)


def as_dict(level: Level) -> dict:
    return {
        "id": level.id,
        "level": level.key,
        "band": level.band,
        "audience": level.audience,
        "bloom": {name: level.bloom[name] for name in BLOOM_ORDER if name in level.bloom},
        "difficulty": {
            name: level.difficulty[name] for name in DIFFICULTY_ORDER if name in level.difficulty
        },
        "time_map": level.time_map,
        "duration_factor": level.duration_factor,
        "task_range": list(level.task_range),
        "scope": level.scope,
        "rubric_posture": level.rubric_posture,
        "may_name_mechanism": level.may_name_mechanism,
        "notes": level.notes,
    }


def counts_for(level: Level, total: int) -> dict[str, dict[str, int]]:
    """Turn the level's percentages into whole question counts for `total`.

    Largest-remainder allocation, so the counts always sum to exactly `total`
    rather than drifting by a question or two after rounding.
    """

    def allocate(percentages: dict[str, int], order: tuple[str, ...]) -> dict[str, int]:
        keys = [name for name in order if percentages.get(name)]
        exact = {name: total * percentages[name] / 100 for name in keys}
        counts = {name: int(value) for name, value in exact.items()}
        remainder = total - sum(counts.values())
        for name in sorted(keys, key=lambda n: exact[n] - counts[n], reverse=True)[:remainder]:
            counts[name] += 1
        return counts

    return {
        "bloom": allocate(level.bloom, BLOOM_ORDER),
        "difficulty": allocate(level.difficulty, DIFFICULTY_ORDER),
    }

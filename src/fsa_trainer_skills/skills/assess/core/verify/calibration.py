"""Compare an assessment's actual shape against its level's defaults.

Every finding here is a **warning**, never an error. Step 0 lets the user
override any level default, and `references/levels.md` says so explicitly, so
drift is worth reporting but never worth failing a run over.

Only what is machine-countable lives here: the Bloom and difficulty mix of a
question set, and the task count of a long-form assessment. Whether the
questions actually sit at the Bloom level their column claims is a judgement
call, and belongs to the verifier agent.
"""

from __future__ import annotations

from ..levels import BLOOM_ORDER, DIFFICULTY_ORDER, Level, counts_for
from .common import CheckResult

#: How far a single bucket may drift before it is worth mentioning. Largest
#: remainder already lands the targets on whole questions, so one question of
#: slack absorbs ordinary rounding without hiding a real miscalibration.
TOLERANCE = 1


def _tally(rows: list[dict[str, str]], column: str, order: tuple[str, ...]) -> dict[str, int]:
    counts = {name: 0 for name in order}
    for row in rows:
        value = row.get(column, "").strip()
        if value in counts:
            counts[value] += 1
    return counts


def _compare(
    axis: str,
    observed: dict[str, int],
    expected: dict[str, int],
    total: int,
    level: Level,
    result: CheckResult,
) -> None:
    drifted = [
        f"{name} {observed.get(name, 0)} vs {expected.get(name, 0)}"
        for name in set(observed) | set(expected)
        if abs(observed.get(name, 0) - expected.get(name, 0)) > TOLERANCE
    ]
    if not drifted:
        return
    result.warn(
        f"{axis} mix differs from the {level.display} default for {total} questions "
        f"(observed vs expected: {', '.join(sorted(drifted))}); "
        f"intentional deviations are fine — say so in the plan echo"
    )


def check_question_set(rows: list[dict[str, str]], level: Level, result: CheckResult) -> None:
    """Warn when the Bloom or difficulty mix drifts from the level default."""
    if not rows:
        return
    total = len(rows)
    expected = counts_for(level, total)
    _compare(
        "Bloom",
        _tally(rows, "Bloom Level", BLOOM_ORDER),
        expected["bloom"],
        total,
        level,
        result,
    )
    _compare(
        "Difficulty",
        _tally(rows, "Difficulty", DIFFICULTY_ORDER),
        expected["difficulty"],
        total,
        level,
        result,
    )


def check_task_count(count: int, level: Level, result: CheckResult) -> None:
    """Warn when a long-form assessment has more or fewer tasks than the level suggests."""
    low, high = level.task_range
    if low <= count <= high:
        return
    result.warn(
        f"{count} tasks; {level.display} suggests {low}-{high}. "
        f"Intentional deviations are fine — say so in the plan echo"
    )

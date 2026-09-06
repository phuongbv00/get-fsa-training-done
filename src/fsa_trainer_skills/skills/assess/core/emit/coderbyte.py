"""Coderbyte multiple-choice import JSON.

Coderbyte marks answers by *position*, and the position that matters is the
first one: **index 0 is always correct**. The vendor template says so in its own
answer text — its multi-answer example lists `correctAnswers: ["2", "3"]` over
answers `["I am correct", "Wrong 2", "Will be correct", "Will be correct"]`, so
the correct set is 0, 2 and 3, not just 2 and 3.

That makes `correctAnswers` *additive* rather than exhaustive, which is easy to
get backwards. Emitting the full correct set while leaving a wrong option at
index 0 silently marks that wrong option correct, and nothing in the import
complains.

So both branches here put a correct option first:

* single answer — correct option leads, no `correctAnswers` key, exactly like
  the template's first example;
* multi answer — a correct option leads, and `correctAnswers` lists the 0-based
  index of *every* correct option, which therefore always includes `"0"`.

Listing index 0 explicitly is redundant under the additive reading and required
under an exhaustive one, so the output is correct either way — worth the one
redundant entry given the cost of being wrong is a silently mis-keyed exam.
"""

from __future__ import annotations

import json
from pathlib import Path

from .master import Question


def build(questions: list[Question]) -> dict:
    out = []
    for question in questions:
        # A correct option always leads, because Coderbyte treats index 0 as
        # correct whether or not it is listed.
        lead = question.correct[0]
        order = [lead] + [n for n in range(1, len(question.options) + 1) if n != lead]
        answers = [question.option(n) for n in order]

        entry: dict = {"question": question.text, "answers": answers}

        if question.is_multi:
            # Map every correct option to its new position. Going through the
            # permutation rather than searching by text keeps this correct when
            # two options happen to read the same.
            position = {original: new for new, original in enumerate(order)}
            indices = sorted(position[n] for n in question.correct)
            entry["correctAnswers"] = [str(i) for i in indices]
            entry["allRequired"] = True

        out.append(entry)
    return {"mc_questions": out}


def render(questions: list[Question]) -> bytes:
    document = json.dumps(build(questions), indent=2, ensure_ascii=False)
    return (document + "\n").encode("utf-8")


def write(questions: list[Question], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(render(questions))
    return len(questions)

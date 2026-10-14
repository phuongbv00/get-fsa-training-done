"""The interactive prompts, driven by a scripted list of keys.

No terminal is involved: every prompt reads keys from a callable and writes to
a stream, so a test hands it `iter([...]).__next__` and a `StringIO`.
"""

from __future__ import annotations

import io

import pytest

from get_fsa_training_done.errors import Cancelled
from get_fsa_training_done.lifecycle import prompt

AGENTS = [
    ("Claude Code", "~/.claude/skills"),
    ("Codex", "~/.codex/skills"),
    ("GitHub Copilot", "~/.copilot/skills"),
    ("Antigravity", "~/.gemini/config/skills"),
]


def keys(*sequence: str):
    return iter(sequence).__next__


def test_multiselect_ticks_with_space_and_confirms_with_enter():
    out = io.StringIO()
    chosen = prompt.multiselect(
        "Which agents?", AGENTS, [0], keys=keys("down", "down", "space", "enter"), out=out
    )
    assert chosen == [0, 2]
    text = out.getvalue()
    assert "↑↓ move, space select, enter confirm" in text
    assert "press 'esc' to exit" in text
    assert "Selected: Claude Code, GitHub Copilot" in text
    assert "Claude Code (~/.claude/skills)" in text


def test_multiselect_unticks_and_wraps_around():
    chosen = prompt.multiselect(
        "Which agents?",
        AGENTS,
        [0, 1],
        keys=keys("space", "up", "space", "enter"),
        out=io.StringIO(),
    )
    # Claude Code unticked; up from the top wraps to Antigravity.
    assert chosen == [1, 3]


def test_multiselect_will_not_confirm_an_empty_selection():
    out = io.StringIO()
    chosen = prompt.multiselect(
        "Which agents?",
        AGENTS,
        [0],
        empty="Select at least one agent",
        keys=keys("space", "enter", "down", "space", "enter"),
        out=out,
    )
    assert chosen == [1]
    assert "Select at least one agent" in out.getvalue()


def test_selected_footer_truncates_like_npx_skills():
    assert prompt.selected_summary(["A", "B", "C"]) == "A, B, C"
    assert prompt.selected_summary(["A", "B", "C", "D", "E"]) == "A, B, C +2 more"


def test_escape_cancels():
    with pytest.raises(Cancelled):
        prompt.multiselect("Which agents?", AGENTS, [0], keys=keys("esc"), out=io.StringIO())
    with pytest.raises(Cancelled):
        prompt.select("Scope", [("User", ""), ("Project", "")], keys=keys("esc"), out=io.StringIO())


def test_ctrl_c_cancels():
    def interrupt():
        raise KeyboardInterrupt

    with pytest.raises(Cancelled):
        prompt.confirm("Proceed?", keys=interrupt, out=io.StringIO())


def test_select_returns_the_cursor():
    options = [("User", ""), ("Project", "")]
    assert prompt.select("Scope", options, keys=keys("enter"), out=io.StringIO()) == 0
    assert prompt.select("Scope", options, keys=keys("down", "enter"), out=io.StringIO()) == 1


@pytest.mark.parametrize(
    ("default", "keys_", "expected"),
    [
        (True, ("enter",), True),
        (False, ("enter",), False),
        (False, ("y",), True),
        (True, ("n",), False),
        (True, ("right", "enter"), False),
        (False, ("left", "x", "enter"), True),
    ],
)
def test_confirm(default, keys_, expected):
    out = io.StringIO()
    assert prompt.confirm("Proceed?", default=default, keys=keys(*keys_), out=out) is expected
    text = out.getvalue()
    assert "● Yes / ○ No" in text or "○ Yes / ● No" in text
    assert ("Yes" if expected else "No") in text.splitlines()[-1]


def test_box_frames_its_lines():
    out = io.StringIO()
    prompt.box("Installation Summary", ["~/.agents/skills/x", "  universal: Codex"], out=out)
    rows = out.getvalue().splitlines()
    assert rows[0].startswith("◇  Installation Summary ─") and rows[0].endswith("┐")
    assert rows[-1].startswith("├") and rows[-1].endswith("┘")
    # Every row is the same width, so the right edge is straight.
    assert len({len(row) for row in rows}) == 1


def test_ascii_fallback_when_the_stream_cannot_encode_the_glyphs():
    out = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
    prompt.multiselect("Which agents?", AGENTS, [0], keys=keys("enter"), out=out)
    out.flush()
    text = out.buffer.getvalue().decode("ascii")
    assert "(*) Claude Code" in text
    assert "( ) Codex" in text


def test_not_interactive_under_ci(monkeypatch):
    monkeypatch.setenv("CI", "true")
    assert prompt.is_interactive() is False

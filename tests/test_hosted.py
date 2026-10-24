"""The ready-made setups for hosted agents in `hosted/`.

They are copied as they are, so a path that stops existing or a prompt that
drifts from its twin reaches users silently.
"""

from __future__ import annotations

from pathlib import Path

from get_fsa_training_done.lifecycle.skillmeta import read_skill_frontmatter
from get_fsa_training_done.skill import SKILL

HOSTED = Path(__file__).resolve().parents[1] / "hosted"
AGENT = HOSTED / "claude-managed-agents" / "agent.md"
COPILOT = HOSTED / "copilot-studio" / "instructions.md"


def _split(path: Path) -> tuple[str, str]:
    """The frontmatter and the body of a Markdown file with `---` fences."""
    _, front, body = path.read_text(encoding="utf-8").split("---\n", 2)
    return front, body.strip()


def _sections(text: str) -> dict[str, str]:
    """Paragraphs keyed by their first line, so twins can be compared by name."""
    return {block.splitlines()[0]: block for block in text.split("\n\n")}


def test_the_agent_attaches_the_skill_the_package_ships():
    front, _ = _split(AGENT)
    skill_line = next(line for line in front.splitlines() if line.strip().startswith("- ../"))
    skill_dir = (AGENT.parent / skill_line.strip()[2:]).resolve()
    assert skill_dir == SKILL.payload_dir.resolve()
    assert read_skill_frontmatter(skill_dir / "SKILL.md")["name"] == SKILL.name


def test_the_agent_names_the_setup_script_the_payload_ships():
    _, body = _split(AGENT)
    assert "scripts/setup.sh" in body
    assert (SKILL.payload_dir / "scripts" / "setup.sh").is_file()


def test_the_copilot_instructions_differ_only_where_there_is_no_shell():
    _, body = _split(AGENT)
    agent = _sections(body)
    copilot = _sections(COPILOT.read_text(encoding="utf-8").strip())
    only_agent = set(agent) - set(copilot)
    only_copilot = set(copilot) - set(agent)
    assert only_agent == {"Working in this sandbox"}
    assert only_copilot == {"Working without a shell"}
    for key in set(agent) & set(copilot):
        assert agent[key] == copilot[key], key

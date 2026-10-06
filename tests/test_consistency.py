"""Gates that stop the repo shipping something internally inconsistent
across the skill payload and the code it describes.

The version lives in several files and the `assessment` skill's level table lives
in two — one for the CLI to read and one for the model to read. Drift between
them is invisible at runtime: a workflow would calibrate to numbers the
verifier does not check against. These run in CI for that reason.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from get_fsa_training_done import features
from get_fsa_training_done.cli import LIFECYCLE_COMMANDS
from get_fsa_training_done.lifecycle.platforms import registry
from get_fsa_training_done.lifecycle.skillmeta import read_skill_frontmatter
from get_fsa_training_done.skill import SKILL

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


@pytest.mark.skipif(not (SCRIPTS / "sync_version.py").exists(), reason="script missing")
def test_version_is_consistent_across_files():
    result = run_script("sync_version.py", "--check")
    assert result.returncode == 0, result.stderr


GENERATORS = sorted(path.relative_to(SCRIPTS).as_posix() for path in SCRIPTS.glob("*/gen_*.py"))


@pytest.mark.parametrize("generator", GENERATORS, ids=lambda g: g.replace("/", ":"))
def test_generated_payload_files_are_current(generator):
    """Every `scripts/<skill>/gen_*.py` in one gate.

    Parametrized over the glob rather than listed, so a new skill's generated
    reference is covered the day it lands — the failure mode otherwise is a
    payload file that quietly stops matching the Python it came from, which
    nothing reports at runtime because the model just reads the stale prose.
    """
    result = run_script(generator, "--check")
    assert result.returncode == 0, result.stderr


def test_there_is_at_least_one_generator():
    """Guards the glob above: an empty parametrization passes vacuously."""
    assert GENERATORS


def test_the_payload_satisfies_codex_rules():
    problems = registry.get("codex").validate(SKILL.payload_dir)
    assert [str(p) for p in problems if p.fatal] == []


def test_the_description_has_no_angle_brackets():
    front = read_skill_frontmatter(SKILL.payload_dir / "SKILL.md")
    assert "<" not in front["description"] and ">" not in front["description"]
    assert len(front["description"]) <= 1024


def test_feature_namespaces_are_distinct_from_lifecycle_commands():
    assert len(set(features.NAMESPACES)) == len(features.NAMESPACES)
    assert not set(features.NAMESPACES) & LIFECYCLE_COMMANDS


def _code_spans(text: str) -> list[str]:
    """Fenced blocks and inline code spans — the only places a command is a command.

    Prose legitimately says "FSA training assessments"; only code is a claim
    about something runnable.
    """
    spans: list[str] = []
    in_fence = False
    fenced: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if in_fence:
                spans.append("\n".join(fenced))
                fenced = []
            in_fence = not in_fence
            continue
        if in_fence:
            fenced.append(line)
        else:
            spans.extend(re.findall(r"`([^`\n]+)`", line))
    return spans


def test_payload_commands_name_a_real_cli_path():
    """`FSA` is the bare CLI, so `FSA <word>` must be a lifecycle command or
    a feature namespace.

    The payloads used to write `FSA verify` for a worker command *and*
    `FSA doctor` for a lifecycle one. Only one of those can be right: worker
    verbs live under a namespace and lifecycle commands do not, so one form
    silently resolved to nothing. Nothing catches that at runtime — the model
    just runs a command that does not exist.
    """
    allowed = LIFECYCLE_COMMANDS | set(features.NAMESPACES)
    offenders = []
    for path in sorted(SKILL.payload_dir.rglob("*.md")):
        for snippet in _code_spans(path.read_text(encoding="utf-8")):
            for match in re.finditer(r"\bFSA ([a-z][a-z-]*)", snippet):
                if match.group(1) not in allowed:
                    offenders.append(f"{path.relative_to(SKILL.payload_dir)}: FSA {match.group(1)}")
    assert offenders == []


#: The only places a feature may reach for an external binary, both optional
#: and allow-listed by path rather than by convention. `.rar` is proprietary
#: and has no pure-Python reader. Docker is the sandbox that runs code which is
#: not ours — a seed script, a submission's tests — so it cannot be in-process.
BINARY_ALLOWLIST = {
    "assessment/core/grading/preprocess.py",
    "assessment/core/sandbox.py",
}


def test_no_feature_shells_out_to_an_external_binary():
    """Every feature does its deterministic work in Python.

    Rendering and archive extraction both used to shell out — to headless
    Chrome and to ditto/unzip/7z — which made the toolchain depend on what
    happened to be installed on a grading or exam machine. They no longer do,
    and this keeps it that way: the failure mode is quiet, because a binary
    that exists on the developer's laptop is invisible until someone else runs
    the command.
    """
    root = Path(features.__file__).parent
    offenders = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if relative in BINARY_ALLOWLIST:
            continue
        source = path.read_text(encoding="utf-8")
        for needle in ("subprocess", "shutil.which", "os.system", "os.exec"):
            if needle in source:
                offenders.append(f"{relative}: {needle}")
    assert offenders == []


# The rename to get-fsa-training-done was a clean break: nothing reads the old
# package, CLI, env var or receipt names. Only the changelog (history) and the
# README's upgrade note may still say them.
OLD_NAMES = ("fsa-trainer" + "-skills", "fsa_trainer" + "_skills", "FSA_TRAINER" + "_SKILLS")
OLD_NAME_ALLOWED = {"CHANGELOG.md", "README.md"}


def test_old_project_name_is_gone():
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, cwd=ROOT, check=True
    ).stdout.split()
    offenders = []
    for name in tracked:
        if name in OLD_NAME_ALLOWED:
            continue
        path = ROOT / name
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        offenders += [f"{name}: {old}" for old in OLD_NAMES if old in text]
    assert offenders == []


# --- The router -----------------------------------------------------------
#
# SKILL.md is the only file the host loads up front; everything else is read
# because a route names it. A file no route reaches is never read, and a route
# naming a missing file fails silently — the model just carries on without it.

ROUTER = SKILL.payload_dir / "SKILL.md"
REFERENCE = re.compile(r"`(references/[A-Za-z0-9_./-]+)`")


def test_the_router_links_every_workflow_file():
    router = ROUTER.read_text(encoding="utf-8")
    unreachable = [
        path.relative_to(SKILL.payload_dir).as_posix()
        for path in sorted((SKILL.payload_dir / "references").rglob("workflows/**/*.md"))
        if path.relative_to(SKILL.payload_dir).as_posix() not in router
    ]
    assert unreachable == []


def test_the_router_links_every_feature_overview():
    router = ROUTER.read_text(encoding="utf-8")
    for namespace in features.NAMESPACES:
        assert f"references/{namespace}/overview.md" in router


def test_references_named_by_the_payload_all_exist():
    missing = []
    for path in sorted(SKILL.payload_dir.rglob("*.md")):
        for match in REFERENCE.finditer(path.read_text(encoding="utf-8")):
            if not (SKILL.payload_dir / match.group(1)).exists():
                missing.append(f"{path.relative_to(SKILL.payload_dir)} -> {match.group(1)}")
    assert missing == []


def test_the_router_names_the_real_cli_and_receipt():
    """The CLI-resolution block is how the model reaches `FSA` at all, and a
    stale name there is invisible: it silently falls through to "not installed"
    and asks the user to install a package that is not this one."""
    from get_fsa_training_done.__about__ import CLI_NAME, PACKAGE_NAME
    from get_fsa_training_done.lifecycle.install.receipt import RECEIPT_NAME

    router = ROUTER.read_text(encoding="utf-8")
    section = router[router.index("## Resolving the CLI") : router.index("## Step 1")]
    assert RECEIPT_NAME in section
    assert f"{CLI_NAME} --version" in section
    assert f"pip install {PACKAGE_NAME}" in section
    assert f"npm install -g {PACKAGE_NAME}" in section


TASK_SECTIONS = ("## Inputs", "## Produces", "## Steps", "## Done when", "## Hands off to")


def _task_files():
    return sorted((SKILL.payload_dir / "references").rglob("tasks/**/*.md"))


def test_there_are_task_blocks():
    assert _task_files()


def test_the_router_links_every_task_file():
    """A task runs on its own when the user asks for one step, so the router
    must be able to reach it directly, not only through a workflow."""
    router = ROUTER.read_text(encoding="utf-8")
    unreachable = [
        path.relative_to(SKILL.payload_dir).as_posix()
        for path in _task_files()
        if path.relative_to(SKILL.payload_dir).as_posix() not in router
    ]
    assert unreachable == []


def test_every_task_follows_the_task_contract():
    """Every block says what it needs, what it makes, and how to tell it is
    done; that is what lets it run alone or inside any workflow."""
    broken = []
    for path in _task_files():
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# Task — "):
            broken.append(f"{path.name}: title")
        positions = [text.find(section) for section in TASK_SECTIONS]
        if -1 in positions or positions != sorted(positions):
            broken.append(f"{path.name}: sections")
    assert broken == []

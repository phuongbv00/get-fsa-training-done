"""`get-fsa-training-done doctor` — is this machine able to run every workflow?

Reports on shared prerequisites (the managed venv and the libraries in it),
whatever each registered skill wants checked, and every skill's payload, which
is validated against Codex's stricter rules regardless of which host it is
installed for.

No skill needs an external binary. The one optional one is a `.rar` extractor:
`.rar` is proprietary and has no pure-Python reader, so a trainee who submits
one needs a tool on PATH. Everything else — rendering, every other archive
format — runs inside the managed environment.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys

from .. import skills as skill_registry
from ..__about__ import CLI_NAME, __version__
from ..envmgr import bootstrap, stamp
from ..platforms import registry

#: Optional, and only for `.rar` — see the module docstring.
RAR_TOOLS = ("unar", "7z", "bsdtar")

#: Imported by the workers inside the managed venv, not by the CLI itself.
VENV_LIBRARIES = (("xhtml2pdf", "assessment render"), ("py7zr", "assessment grade preprocess"))


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "doctor",
        help="check this machine for everything every skill's workflows need",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    archives = {tool: shutil.which(tool) or "" for tool in RAR_TOOLS}
    env = bootstrap.info()

    extra: dict[str, str] = {}
    payloads: dict[str, dict] = {}
    for skill in skill_registry.all_skills():
        try:
            problems = [str(p) for p in registry.get("codex").validate(skill.payload_dir)]
        except Exception as exc:  # pragma: no cover - packaging failure
            problems = [f"ERROR: payload unavailable: {exc}"]
        payloads[skill.namespace] = {
            "name": skill.name,
            "path": str(skill.payload_dir),
            "problems": problems,
        }
        extra.update(skill.doctor_extra())

    superseded = _find_superseded()
    libraries = {module: _importable(module) for module, _ in VENV_LIBRARIES}

    report = {
        "package_version": __version__,
        "python": {
            "executable": sys.executable,
            "version": ".".join(str(p) for p in sys.version_info[:3]),
            "base": stamp.base_python(),
        },
        "uv": env["uv"],
        "environment_home": env["home"],
        "environments": env["groups"],
        "extra": extra,
        "rar_tools": archives,
        "libraries": libraries,
        "payloads": payloads,
        "superseded": superseded,
    }

    if args.as_json:
        print(json.dumps(report, indent=2))
        return 0 if _healthy(report) else 1

    print(f"{CLI_NAME} {__version__}")
    print(f"  python           {report['python']['version']}  ({report['python']['executable']})")
    print(f"  uv               {env['uv'] or 'not found (falling back to python -m venv)'}")
    print(f"  env home         {env['home']}")
    for group, info in env["groups"].items():
        state = "ready" if info["ready"] else "not built yet (built on first use)"
        print(f"  env:{group:<12} {state}")

    for module, used_by in VENV_LIBRARIES:
        state = "installed" if libraries[module] else f"MISSING — `{used_by}` needs it"
        print(f"  lib:{module:<13} {state}")
    if not all(libraries.values()):
        print("                   run `get-fsa-training-done install` to build the environment")

    for key, value in sorted(extra.items()):
        print(f"  {key:<16} {value or 'not found'}")

    available = [tool for tool, path in archives.items() if path]
    if available:
        print(f"  rar extractor    {', '.join(available)} (optional)")
    else:
        print("  rar extractor    none (optional) — a .rar submission cannot be opened")
        print("                   install one of: " + ", ".join(RAR_TOOLS))
        print("                   every other format is handled without it")

    for info in payloads.values():
        state = "valid" if not info["problems"] else "; ".join(info["problems"])
        print(f"  payload:{info['name']:<24} {state}")

    for row in superseded:
        print(f"  superseded       {row['previous_name']} at {row['dest']}")
        print(
            f"                   still loaded by {row['label']}; "
            f"installing {row['skill']} clears it"
        )

    return 0 if _healthy(report) else 1


def _find_superseded() -> list[dict]:
    """Installs left under a name a skill used to have.

    Worth a line in `doctor` because the symptom is confusing rather than
    loud: the host keeps loading the old copy, so the agent sees two skills
    offering the same thing and picks unpredictably between them.
    """
    from ..install import legacy

    found: list[dict] = []
    for skill in skill_registry.all_skills():
        if not skill.previous_names:
            continue
        for platform in registry.resolve(registry.ALL):
            for scope in ("user", "project"):
                if scope == "project" and not platform.project_subdir:
                    continue
                dest = platform.dest(scope, skill.name)
                for item in legacy.find(skill, platform, scope, None, current_dest=dest):
                    if any(row["dest"] == str(item.dest) for row in found):
                        continue
                    found.append(
                        {
                            "skill": skill.name,
                            "skill_namespace": skill.namespace,
                            "previous_name": item.name,
                            "platform": platform.key,
                            "label": platform.label,
                            "dest": str(item.dest),
                        }
                    )
    return found


def _importable(module: str) -> bool:
    """Is the library present *for the interpreter that will run the workers*?

    `doctor` runs in whichever interpreter invoked it, which is not the managed
    venv, so this is a best-effort signal rather than proof. It catches the case
    that actually bites — the environment was never built.
    """
    from importlib.util import find_spec

    try:
        return find_spec(module) is not None
    except (ImportError, ValueError):  # pragma: no cover - malformed install
        return False


def _healthy(report: dict) -> bool:
    """Exit status.

    A missing `.rar` extractor is optional and never fails the check — it is one
    archive format, and the machine handles every other one unaided. A broken
    payload does fail: that is shipped content, not a local prerequisite.
    """
    for info in report["payloads"].values():
        if any(p.startswith("ERROR") for p in info["problems"]):
            return False
    return True

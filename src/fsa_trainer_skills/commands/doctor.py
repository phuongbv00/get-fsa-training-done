"""`fsa-trainer-skills doctor` — is this machine able to run every workflow?

Reports on shared prerequisites (the managed venv) plus whatever each
registered skill wants checked — e.g. the `assess` skill reports the Chrome
binary its `render` command needs, and every skill's payload is validated
against Codex's stricter rules regardless of which host it's installed for.
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

#: `grade preprocess` (the assess skill) tries these in order per archive type.
ARCHIVE_TOOLS = ("ditto", "unzip", "bsdtar", "7z", "unar")


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "doctor",
        help="check this machine for everything every skill's workflows need",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    archives = {tool: shutil.which(tool) or "" for tool in ARCHIVE_TOOLS}
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
        "archive_tools": archives,
        "payloads": payloads,
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

    chrome = extra.get("chrome", "")
    if chrome:
        print(f"  chrome           {chrome}")
    elif "chrome" in extra:
        print("  chrome           NOT FOUND — `assess render` cannot export a PDF")
        print("                   install Chrome/Chromium/Edge, or set CHROME_BIN")

    available = [tool for tool, path in archives.items() if path]
    if available:
        print(f"  archive tools    {', '.join(available)}")
    else:
        print("  archive tools    NONE — `assess grade preprocess` cannot extract submissions")
        print("                   install one of: " + ", ".join(ARCHIVE_TOOLS))
    if not archives.get("bsdtar") and not archives.get("7z") and not archives.get("unar"):
        print("  note             .rar/.7z submissions need bsdtar, 7z, or unar")

    for info in payloads.values():
        state = "valid" if not info["problems"] else "; ".join(info["problems"])
        print(f"  payload:{info['name']:<24} {state}")

    return 0 if _healthy(report) else 1


def _healthy(report: dict) -> bool:
    for info in report["payloads"].values():
        if any(p.startswith("ERROR") for p in info["problems"]):
            return False
    if "chrome" in report["extra"] and not report["extra"]["chrome"]:
        return False
    return any(report["archive_tools"].values())

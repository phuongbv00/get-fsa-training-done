#!/usr/bin/env python3
"""Propagate the canonical version out to the files that duplicate it.

`src/get_fsa_training_done/__about__.py` is the single source of truth.
`pyproject.toml` reads it directly through hatchling, but `package.json` and
the skill payload's `VERSION` file cannot, so they are written here. `--check`
runs in CI so drift fails the build instead of shipping.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from get_fsa_training_done.skill import SKILL  # noqa: E402

ABOUT = ROOT / "src" / "get_fsa_training_done" / "__about__.py"
PACKAGE_JSON = ROOT / "package.json"


def canonical_version() -> str:
    match = re.search(
        r'^__version__\s*=\s*"([^"]+)"', ABOUT.read_text(encoding="utf-8"), re.MULTILINE
    )
    if not match:
        raise SystemExit(f"ERROR: no __version__ found in {ABOUT}")
    return match.group(1)


def sync_package_json(version: str, *, check: bool) -> list[str]:
    text = PACKAGE_JSON.read_text(encoding="utf-8")
    current = json.loads(text).get("version")
    if current == version:
        return []
    if check:
        return [f"package.json is {current}, expected {version}"]
    PACKAGE_JSON.write_text(
        re.sub(r'("version":\s*")[^"]+(")', rf"\g<1>{version}\g<2>", text, count=1),
        encoding="utf-8",
    )
    return []


def sync_payload_versions(version: str, *, check: bool) -> list[str]:
    problems: list[str] = []
    for skill in (SKILL,):
        target = skill.payload_dir / "VERSION"
        current = target.read_text(encoding="utf-8").strip() if target.is_file() else ""
        if current == version:
            continue
        if check:
            problems.append(
                f"{target.relative_to(ROOT)} is {current or 'missing'}, expected {version}"
            )
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(version + "\n", encoding="utf-8")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift instead of fixing it")
    args = parser.parse_args()

    version = canonical_version()
    problems = sync_package_json(version, check=args.check) + sync_payload_versions(
        version, check=args.check
    )

    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        print("run `python scripts/sync_version.py` to fix", file=sys.stderr)
        return 1

    print(f"version {version} is consistent" if args.check else f"synced version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

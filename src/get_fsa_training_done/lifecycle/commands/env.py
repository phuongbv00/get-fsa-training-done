"""`gftd env` — inspect, build, or delete the managed virtualenvs."""

from __future__ import annotations

import argparse
import json

from ..envmgr import bootstrap, stamp


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "env",
        help="inspect or manage the virtualenv the workers run in",
    )
    sub = parser.add_subparsers(dest="env_command", required=True)

    info = sub.add_parser("info", help="show environment locations and readiness")
    info.add_argument("--json", action="store_true", dest="as_json")
    info.set_defaults(func=run_info)

    ensure = sub.add_parser("ensure", help="build the environment now")
    ensure.add_argument(
        "--group",
        action="append",
        choices=list(stamp.GROUPS),
        help="dependency group (repeatable; default: all)",
    )
    ensure.add_argument("--offline", action="store_true")
    ensure.set_defaults(func=run_ensure)

    purge = sub.add_parser("purge", help="delete every managed environment")
    purge.set_defaults(func=run_purge)


def run_info(args: argparse.Namespace) -> int:
    info = bootstrap.info()
    if getattr(args, "as_json", False):
        print(json.dumps(info, indent=2))
        return 0
    print(f"home         {info['home']}")
    print(f"base python  {info['base_python']}")
    print(f"uv           {info['uv'] or 'not found'}")
    print(f"re-exec      {'inside the managed venv' if info['in_venv'] else 'not active'}")
    for group, data in info["groups"].items():
        state = "ready" if data["ready"] else "not built"
        requirements = ", ".join(data["requirements"]) or "(no third-party packages)"
        print(f"\n[{group}] {state}")
        print(f"  path         {data['path']}")
        print(f"  requirements {requirements}")
    return 0


def run_ensure(args: argparse.Namespace) -> int:
    groups = args.group or list(stamp.GROUPS)
    for group in groups:
        path = bootstrap.ensure(group, offline=args.offline)
        print(f"[{group}] ready at {path}")
    return 0


def run_purge(args: argparse.Namespace) -> int:
    removed = bootstrap.purge()
    if not removed:
        print("nothing to remove")
        return 0
    for path in removed:
        print(f"removed {path}")
    return 0

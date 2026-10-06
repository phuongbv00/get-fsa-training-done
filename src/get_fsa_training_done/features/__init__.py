"""The worker namespaces: `program`, `material` and `assessment`.

Each feature package exports `NAMESPACE`, `add_parsers(subparsers)` and,
optionally, `doctor_extra()`. Adding a feature means adding it to `FEATURES`.
"""

from __future__ import annotations

import argparse

from . import assessment, material, program

FEATURES = (program, material, assessment)
NAMESPACES = tuple(feature.NAMESPACE for feature in FEATURES)


def add_parsers(subparsers: argparse._SubParsersAction) -> None:
    for feature in FEATURES:
        feature.add_parsers(subparsers)


def doctor_extra() -> dict[str, str]:
    extra: dict[str, str] = {}
    for feature in FEATURES:
        report = getattr(feature, "doctor_extra", None)
        if report is not None:
            extra.update(report())
    return extra


__all__ = ["FEATURES", "NAMESPACES", "add_parsers", "doctor_extra"]

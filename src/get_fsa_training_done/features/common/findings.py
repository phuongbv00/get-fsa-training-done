"""Findings, carrying the rule that produced them.

Shared, beside `levels.py`, because two features check many artifacts in one
run: a programme spans seven topics, a module spans a dozen lecture notes. The
assessment feature's `CheckResult` collects bare strings, which is right when a
run checks a single artifact; here a finding has to name *where* it was found
and *which rule* fired, so a failure is a lookup in that feature's generated
rule reference rather than a paragraph to interpret.

The rule ids are not shared — each feature owns its own vocabulary and its own
generated reference. Only the shape of a finding is common.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    where: str
    message: str

    def line(self) -> str:
        return f"[{self.rule}] {self.where}: {self.message}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    #: Derived facts worth printing whether or not anything failed — the whole
    #: point is that these were computed, not assumed.
    facts: dict = field(default_factory=dict)

    def add(self, rule: str, severity: str, where: str, message: str) -> None:
        self.findings.append(Finding(rule, severity, where, message))

    def error(self, rule: str, where: str, message: str) -> None:
        self.add(rule, ERROR, where, message)

    def warn(self, rule: str, where: str, message: str) -> None:
        self.add(rule, WARNING, where, message)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors

    def rules_fired(self) -> set[str]:
        return {f.rule for f in self.findings}

    def report(self, label: str, *, strict: bool = False) -> int:
        failed = self.errors or (strict and self.warnings)
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        for name, value in self.facts.items():
            print(f"  {name}: {value}")
        for finding in self.errors:
            print(f"ERROR: {finding.line()}")
        for finding in self.warnings:
            print(f"WARNING: {finding.line()}")
        return 1 if failed else 0

    def as_json(self, label: str, *, strict: bool = False) -> str:
        failed = bool(self.errors or (strict and self.warnings))
        return json.dumps(
            {
                "label": label,
                "ok": not failed,
                "facts": self.facts,
                "findings": [
                    {
                        "rule": f.rule,
                        "severity": f.severity,
                        "where": f.where,
                        "message": f.message,
                    }
                    for f in self.findings
                ],
            },
            indent=2,
            ensure_ascii=False,
        )


__all__ = ["ERROR", "WARNING", "Finding", "Report"]

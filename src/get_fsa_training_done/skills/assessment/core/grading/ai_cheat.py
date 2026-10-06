"""Deterministic signals that a submission may not be the learner's own work.

Renamed from the original `integrity_signals`, which read as data integrity.
What this actually collects is evidence of AI authorship and of shared sources:

- source, comment, and Javadoc volume;
- characters no keyboard layout produces (em dash, arrow, ellipsis, curly
  quotes), which arrive by paste rather than by typing;
- comments that only narrate the code or repeat the endpoint mapping above them;
- clustered file modification times;
- placeholders sitting alongside generated output artifacts;
- byte-identical files and trees across submissions;
- corresponding files with identical token streams once comments and string
  literals are removed, which catches comment-stripped copies.

**None of this proves anything and none of it touches a grade.** It produces a
ranked list for a human to review, and the two questions it can inform — "was
this AI-written" and "did these two share a source" — are kept separate,
because the evidence for each is different.

The non-keyboard character set is calibrated to the Vietnamese and US layouts
these learners type on.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from .plagiarism import LANG_BY_EXT, TOKEN, strip_noise
from .roster import std_id_from_folder

SOURCE_EXTENSIONS = set(LANG_BY_EXT) | {".xml"}
SKIP_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__MACOSX",
    "_plagiarism",
    "_scores",
    "_ai_cheat",
    "bin",
    "build",
    "data",
    "dist",
    "node_modules",
    "out",
    "output",
    "target",
    "vendor",
}

PLACEHOLDER = re.compile(
    r"\b(?:TODO|FIXME|Not\s+yet\s+implemented|UnsupportedOperationException)\b", re.I
)

#: Characters a Vietnamese or US keyboard layout does not produce directly, so
#: their presence means pasted text. An IDE's smart-punctuation substitution can
#: also introduce the dash and quote forms, which is why this is reported with
#: samples for a reviewer rather than treated as a finding.
NON_KEYBOARD = {
    "—": "em dash",
    "–": "en dash",
    "→": "right arrow",
    "⇒": "double arrow",
    "…": "ellipsis",
    "‘": "left curly quote",
    "’": "right curly quote",
    "“": "left curly dquote",
    "”": "right curly dquote",
    "×": "multiplication sign",
    "≥": "greater-or-equal",
    "≤": "less-or-equal",
    "•": "bullet",
    " ": "non-breaking space",
}

ENDPOINT_NARRATION = re.compile(r"(?:GET|POST|PUT|PATCH|DELETE)\s+/\S*", re.I)
DECLARATION = re.compile(
    r"\b(?:public|private|protected)\b.*?\b(\w+)\s*\(|"
    r"\b(?:class|interface|enum|record)\s+(\w+)|"
    r"\.(\w+)\s*\(",
)
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+")
#: A "comment" that is really commented-out code is dead code, not narration.
CODE_LIKE = re.compile(r"[;{}=]|\w\s*\(|^@\w|\breturn\b|\bimport\b|\bnew\b")


def split_identifier(name: str) -> set[str]:
    """camelCase / PascalCase / snake_case into a lowercase word set."""
    parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).replace("_", " ")
    return {word.lower() for word in WORD.findall(parts)}


def comment_narration_metrics(text: str) -> dict:
    """Count comments that merely restate the code they sit next to."""
    lines = text.splitlines()
    endpoint = echo = total = 0
    samples: list[str] = []

    for index, raw in enumerate(lines):
        stripped = raw.strip()
        at = stripped.find("//")
        if at < 0:
            continue
        body = stripped[at + 2 :].strip()
        if len(body) < 8:
            continue
        total += 1

        # The code being described: the same line for an inline comment, or the
        # next real line for a leading one.
        if at > 0:
            target = stripped[:at]
        else:
            target = ""
            for following in lines[index + 1 :]:
                candidate = following.strip()
                if not candidate or candidate.startswith(("//", "*", "/*")):
                    continue
                target = candidate
                break
        if not target:
            continue

        if ENDPOINT_NARRATION.search(body) and (
            "Mapping" in target or ENDPOINT_NARRATION.search(target)
        ):
            endpoint += 1
            if len(samples) < 4:
                samples.append(body[:90])
            continue

        if CODE_LIKE.search(body):
            continue

        code_words: set[str] = set()
        for match in DECLARATION.finditer(target):
            for group in match.groups():
                if group:
                    code_words |= split_identifier(group)
        for token in WORD.findall(target):
            code_words |= split_identifier(token)
        if not code_words:
            continue

        comment_words = {word.lower() for word in WORD.findall(body)}
        # One or two words is too thin to call narration.
        if len(comment_words) < 3:
            continue
        if comment_words <= code_words:
            echo += 1
            if len(samples) < 4:
                samples.append(body[:90])

    return {
        "comments_scanned": total,
        "endpoint_narration": endpoint,
        "echo_narration": echo,
        "narration_samples": samples,
    }


def non_keyboard_metrics(text: str) -> dict[str, int]:
    found: dict[str, int] = defaultdict(int)
    for character, label in NON_KEYBOARD.items():
        count = text.count(character)
        if count:
            found[label] += count
    return dict(found)


def iter_source_files(folder: Path):
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name.startswith("._"):
            continue
        relative = path.relative_to(folder)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() in SOURCE_EXTENSIONS:
            yield path


def normalized_tokens(text: str, extension: str) -> list[str]:
    lang = "xml" if extension == ".xml" else LANG_BY_EXT.get(extension, "text")
    return TOKEN.findall(strip_noise(text, lang).lower())


def line_metrics(text: str) -> dict:
    code = comment = inline = long_comment = 0
    in_block = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        is_comment = False
        if in_block:
            is_comment = True
            if "*/" in stripped:
                in_block = False
        elif stripped.startswith(("//", "#", "--", "/*", "*", "*/")):
            is_comment = True
            if stripped.startswith("/*") and "*/" not in stripped:
                in_block = True
        else:
            code += 1
            if "//" in stripped or "/*" in stripped:
                inline += 1

        if is_comment:
            comment += 1
            if len(stripped) >= 80:
                long_comment += 1

    return {
        "code_lines": code,
        "comment_lines": comment,
        "inline_comment_lines": inline,
        "long_comment_lines": long_comment,
    }


def output_file_count(folder: Path) -> int:
    output = folder / "output"
    if not output.is_dir():
        return 0
    return sum(1 for path in output.rglob("*") if path.is_file())


def build_student_metrics(
    folder: Path,
    *,
    total_score: float | None = None,
    min_tokens: int = 40,
) -> tuple[dict, dict]:
    files: dict[str, dict] = {}
    totals = {
        "source_files": 0,
        "source_lines": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "inline_comment_lines": 0,
        "long_comment_lines": 0,
        "javadoc_blocks": 0,
        "placeholder_lines": 0,
        "comments_scanned": 0,
        "endpoint_narration": 0,
        "echo_narration": 0,
        "non_keyboard_chars": 0,
    }
    non_keyboard: dict[str, int] = defaultdict(int)
    non_keyboard_files: set[str] = set()
    narration_samples: list[str] = []
    narration_files: set[str] = set()
    mtimes: list[float] = []
    mtimes_by_extension: dict[str, list[float]] = defaultdict(list)

    for path in iter_source_files(folder):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        relative = str(path.relative_to(folder))
        metrics = line_metrics(text)
        tokens = normalized_tokens(text, path.suffix.lower())

        totals["source_files"] += 1
        totals["source_lines"] += len(text.splitlines())
        totals["javadoc_blocks"] += text.count("/**")
        totals["placeholder_lines"] += sum(
            1 for line in text.splitlines() if PLACEHOLDER.search(line)
        )
        for key, value in metrics.items():
            totals[key] += value

        narration = comment_narration_metrics(text)
        for key in ("comments_scanned", "endpoint_narration", "echo_narration"):
            totals[key] += narration[key]
        if narration["endpoint_narration"] or narration["echo_narration"]:
            narration_files.add(relative)
            for sample in narration["narration_samples"]:
                if len(narration_samples) < 6:
                    narration_samples.append(f"{relative}: {sample}")

        for label, count in non_keyboard_metrics(text).items():
            non_keyboard[label] += count
            totals["non_keyboard_chars"] += count
            non_keyboard_files.add(relative)

        modified = path.stat().st_mtime
        mtimes.append(modified)
        mtimes_by_extension[path.suffix.lower()].append(modified)
        files[relative] = {
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "tokens": tokens if len(tokens) >= min_tokens else None,
        }

    code = totals["code_lines"]
    totals["comment_to_code_ratio"] = round(totals["comment_lines"] / code, 3) if code else 0.0
    narrating = totals["endpoint_narration"] + totals["echo_narration"]
    totals["narration_comments"] = narrating
    totals["narration_ratio"] = (
        round(narrating / totals["comments_scanned"], 3) if totals["comments_scanned"] else 0.0
    )
    totals["narration_files"] = len(narration_files)
    totals["narration_samples"] = narration_samples
    totals["non_keyboard_by_kind"] = dict(sorted(non_keyboard.items()))
    totals["non_keyboard_files"] = len(non_keyboard_files)
    totals["unique_source_mtimes"] = len(set(mtimes))
    totals["mtime_span_seconds"] = round(max(mtimes) - min(mtimes), 3) if mtimes else 0.0

    if mtimes_by_extension:
        extension, values = max(
            mtimes_by_extension.items(), key=lambda item: (len(item[1]), item[0])
        )
        totals["dominant_source_extension"] = extension
        totals["dominant_source_files"] = len(values)
        totals["dominant_unique_mtimes"] = len(set(values))
        totals["dominant_mtime_span_seconds"] = round(max(values) - min(values), 3)
    else:
        totals["dominant_source_extension"] = ""
        totals["dominant_source_files"] = 0
        totals["dominant_unique_mtimes"] = 0
        totals["dominant_mtime_span_seconds"] = 0.0

    totals["output_files"] = output_file_count(folder)
    totals["placeholder_output_mismatch_hint"] = bool(
        totals["placeholder_lines"] and totals["output_files"]
    )
    if total_score is not None:
        totals["total_score"] = total_score
    return totals, files


def compare_students(student_files: dict[str, dict]) -> list[dict]:
    ids = sorted(student_files)
    pairs: list[dict] = []

    for index, first in enumerate(ids):
        for second in ids[index + 1 :]:
            left, right = student_files[first], student_files[second]
            left_paths, right_paths = set(left), set(right)
            common = sorted(left_paths & right_paths)

            exact = [path for path in common if left[path]["sha256"] == right[path]["sha256"]]
            comparable = [
                path
                for path in common
                if left[path]["tokens"] is not None and right[path]["tokens"] is not None
            ]
            normalized_equal = [
                path for path in comparable if left[path]["tokens"] == right[path]["tokens"]
            ]

            exact_tree = (
                bool(left_paths) and left_paths == right_paths and len(exact) == len(left_paths)
            )
            normalized_tree = (
                bool(comparable)
                and left_paths == right_paths
                and len(normalized_equal) == len(comparable)
            )
            exact_ratio = len(exact) / len(common) if common else 0.0
            normalized_ratio = len(normalized_equal) / len(comparable) if comparable else 0.0

            if (
                exact_tree
                or normalized_tree
                or (len(comparable) >= 5 and normalized_ratio >= 0.8)
                or (len(common) >= 5 and exact_ratio >= 0.5)
            ):
                pairs.append(
                    {
                        "a": first,
                        "b": second,
                        "common_files": len(common),
                        "exact_files": len(exact),
                        "exact_file_ratio": round(exact_ratio, 3),
                        "comparable_normalized_files": len(comparable),
                        "normalized_equal_files": len(normalized_equal),
                        "normalized_equal_ratio": round(normalized_ratio, 3),
                        "exact_source_tree": exact_tree,
                        "normalized_source_tree": normalized_tree,
                        "comment_or_string_stripped_copy_hint": normalized_tree and not exact_tree,
                        "example_exact_files": exact[:5],
                        "example_normalized_equal_files": normalized_equal[:5],
                    }
                )

    pairs.sort(
        key=lambda pair: (
            pair["normalized_equal_ratio"],
            pair["exact_file_ratio"],
            pair["normalized_equal_files"],
        ),
        reverse=True,
    )
    return pairs


def load_selected_scores(score_dirs: list[Path], min_score: float) -> dict[str, float]:
    selected: dict[str, float] = {}
    for directory in score_dirs:
        for path in sorted(Path(directory).glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            std_id = (data.get("std_id") or path.stem).strip()
            try:
                total = float(data.get("total"))
            except (TypeError, ValueError):
                continue
            if std_id and total >= min_score:
                selected[std_id] = total
    return selected


@dataclass
class Report:
    payload: dict
    text: str


def run(
    *,
    preprocessed: list[Path],
    subject: str,
    submission_type: str,
    score_dirs: list[Path] | None = None,
    min_score: float = 0.0,
    min_tokens: int = 40,
) -> Report:
    for path in preprocessed:
        if not path.is_dir():
            raise UsageError(f"not a directory: {path}")

    score_dirs = score_dirs or []
    selected = load_selected_scores(score_dirs, min_score)
    filter_by_score = bool(score_dirs)

    metrics_by_student: dict[str, dict] = {}
    files_by_student: dict[str, dict] = {}

    for tree in preprocessed:
        for folder in sorted(tree.iterdir()):
            if not folder.is_dir() or folder.name.startswith("_"):
                continue
            std_id = std_id_from_folder(folder.name, subject, submission_type)
            if filter_by_score and std_id not in selected:
                continue
            if std_id in metrics_by_student:
                raise UsageError(f"student id {std_id} appears in more than one preprocessed tree")
            metrics, files = build_student_metrics(
                folder,
                total_score=selected.get(std_id),
                min_tokens=min_tokens,
            )
            metrics_by_student[std_id] = metrics
            files_by_student[std_id] = files

    payload = {
        "preprocessed": [str(path) for path in preprocessed],
        "score_dirs": [str(path) for path in score_dirs],
        "params": {"min_score": min_score, "min_tokens": min_tokens},
        "students": dict(sorted(metrics_by_student.items())),
        "pair_signals": compare_students(files_by_student),
        "interpretation_warning": (
            "These signals do not prove AI use or cheating. Keep confidence in AI "
            "assistance separate from confidence in a shared or non-independent source, "
            "and never let either change a grade on its own."
        ),
    }
    return Report(payload=payload, text=render(payload))


def render(payload: dict) -> str:
    lines = [
        "# AI-authorship and shared-source signals (INSTRUCTOR ONLY)",
        "",
        "These signals do not prove AI use or cheating, and must not change a grade.",
        "Keep confidence in AI assistance separate from confidence in a shared source.",
        "",
        f"Students examined: {len(payload['students'])}",
        f"Minimum score filter: {payload['params']['min_score']}",
        "",
        "## Per-student volume",
        "",
    ]
    for std_id, metrics in payload["students"].items():
        score = metrics.get("total_score")
        score_text = f" score={score:g}" if score is not None else ""
        lines.append(
            f"- {std_id}:{score_text} files={metrics['source_files']} "
            f"code={metrics['code_lines']} comments={metrics['comment_lines']} "
            f"comment/code={metrics['comment_to_code_ratio']} "
            f"javadocs={metrics['javadoc_blocks']} "
            f"dominant={metrics['dominant_source_extension']}"
            f"/{metrics['dominant_source_files']} "
            f"dominant-mtime-span={metrics['dominant_mtime_span_seconds']}s "
            f"placeholders={metrics['placeholder_lines']} "
            f"output-files={metrics['output_files']}"
        )

    lines += [
        "",
        "## AI-authorship indicators",
        "",
        "Non-keyboard characters cannot be typed on the layouts these learners use, so",
        "they arrive by paste — though an IDE's smart-punctuation substitution can also",
        "produce the dash and quote forms. Narration counts comments that only repeat",
        "the endpoint mapping or the identifiers on the line they describe.",
        "",
    ]
    for std_id, metrics in payload["students"].items():
        kinds = metrics.get("non_keyboard_by_kind") or {}
        rendered = ", ".join(f"{k}x{v}" for k, v in kinds.items()) if kinds else "none"
        lines.append(
            f"- {std_id}: non-keyboard={metrics.get('non_keyboard_chars', 0)}"
            f" in {metrics.get('non_keyboard_files', 0)} file(s) [{rendered}]"
            f" | narration={metrics.get('narration_comments', 0)}"
            f"/{metrics.get('comments_scanned', 0)}"
            f" (ratio {metrics.get('narration_ratio', 0)},"
            f" endpoint {metrics.get('endpoint_narration', 0)},"
            f" echo {metrics.get('echo_narration', 0)})"
            f" across {metrics.get('narration_files', 0)} file(s)"
        )
        for sample in (metrics.get("narration_samples") or [])[:3]:
            lines.append(f"    e.g. {sample}")

    lines += ["", "## Shared-source pair signals", ""]
    if not payload["pair_signals"]:
        lines.append("No corresponding-file pairs met the signal thresholds.")
    else:
        for pair in payload["pair_signals"]:
            flags = []
            if pair["exact_source_tree"]:
                flags.append("exact tree")
            if pair["normalized_source_tree"]:
                flags.append("normalized tree")
            if pair["comment_or_string_stripped_copy_hint"]:
                flags.append("possible comment/string-stripped copy")
            suffix = f" [{', '.join(flags)}]" if flags else ""
            lines.append(
                f"- {pair['a']} <-> {pair['b']}: "
                f"exact={pair['exact_files']}/{pair['common_files']}, "
                f"normalized={pair['normalized_equal_files']}/"
                f"{pair['comparable_normalized_files']}{suffix}"
            )

    lines += [
        "",
        "Modification-time clustering is supporting evidence only: archive and copy",
        "tools may preserve or normalise timestamps.",
        "",
    ]
    return "\n".join(lines)


def write(report: Report, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "ai_cheat_signals.json"
    text_path = out_dir / "ai_cheat_report.txt"
    json_path.write_text(json.dumps(report.payload, indent=2, ensure_ascii=False), encoding="utf-8")
    text_path.write_text(report.text, encoding="utf-8")
    return json_path, text_path

"""Similarity detection across preprocessed submissions (instructor-only).

MOSS-style winnowing: normalise each file into a token stream (comments and
string literals stripped, so renaming and reformatting cannot hide copying),
build k-gram shingles, hash them, and keep a stable subset per sliding window.
Two students are compared per language family, so SQL is only ever compared to
SQL.

Reported per pair:

    similarity  = |A n B| / |A u B|          Jaccard
    containment = |A n B| / min(|A|, |B|)    catches "copied a subset"

High similarity is a **signal to review by hand, not proof**, and nothing here
feeds a grade.

One deliberate change from the original script: fingerprints use a stable hash
rather than the builtin `hash()`. Python randomises string hashing per process,
so the old fingerprints were only comparable within a single run — two runs over
the same submissions produced different numbers, which makes a flagged pair
impossible to re-check later.
"""

from __future__ import annotations

import json
import re
import zlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from fsa_trainer_skills.errors import UsageError

from .roster import std_id_from_folder

#: Files are only compared within the same language family.
LANG_BY_EXT = {
    ".sql": "sql",
    ".js": "js",
    ".jsx": "js",
    ".mjs": "js",
    ".cjs": "js",
    ".ts": "ts",
    ".tsx": "ts",
    ".java": "java",
    ".py": "py",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cs": "cs",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "css",
    ".php": "php",
    ".go": "go",
    ".rb": "rb",
    ".md": "text",
    ".txt": "text",
    ".json": "json",
}

SKIP_DIRS = {
    "node_modules",
    ".git",
    "__MACOSX",
    "dist",
    "build",
    "target",
    "out",
    ".idea",
    ".vscode",
    "vendor",
    "_scores",
    "_plagiarism",
    "_ai_cheat",
}

BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
LINE_SLASH = re.compile(r"//[^\n]*")
LINE_HASH = re.compile(r"#[^\n]*")
LINE_SQL = re.compile(r"--[^\n]*")
STRINGS = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`")
TOKEN = re.compile(r"[A-Za-z_]\w+|[0-9]+|[^\sA-Za-z0-9_]")

DEFAULTS = {
    "threshold": 0.5,
    "containment": 0.7,
    "k": 5,
    "window": 4,
    "min_tokens": 40,
}


def stable_hash(text: str) -> int:
    """Deterministic across processes and Python versions, unlike `hash()`."""
    return zlib.crc32(text.encode("utf-8")) & 0xFFFFFFFF


def strip_noise(text: str, lang: str) -> str:
    """Drop comments and string literals so wording cannot mask copying."""
    text = BLOCK_COMMENT.sub(" ", text)
    if lang == "html":
        text = HTML_COMMENT.sub(" ", text)
    if lang in {"js", "ts", "java", "c", "cpp", "cs", "php", "go", "css"}:
        text = LINE_SLASH.sub(" ", text)
    if lang in {"py", "rb"}:
        text = LINE_HASH.sub(" ", text)
    if lang == "sql":
        text = LINE_SQL.sub(" ", text)
    return STRINGS.sub(' "" ', text)


def tokenize(text: str, lang: str) -> list[str]:
    return TOKEN.findall(strip_noise(text.lower(), lang))


def fingerprints(tokens: list[str], k: int, window: int) -> set[int]:
    """k-gram hashes, winnowed to the rightmost minimum of each window."""
    if len(tokens) < k:
        return {stable_hash(" ".join(tokens))} if tokens else set()

    hashes = [stable_hash(" ".join(tokens[i : i + k])) for i in range(len(tokens) - k + 1)]
    if len(hashes) < window:
        return set(hashes)

    selected: set[int] = set()
    previous = -1
    for i in range(len(hashes) - window + 1):
        chunk = hashes[i : i + window]
        smallest = min(chunk)
        position = i + (len(chunk) - 1 - chunk[::-1].index(smallest))
        if position != previous:
            selected.add(hashes[position])
            previous = position
    return selected


def iter_files(folder: Path, extensions: set[str]):
    for path in sorted(folder.rglob("*")):
        if path.is_dir() or path.name.startswith("._"):
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(folder).parts):
            continue
        if path.suffix.lower() in extensions:
            yield path


def build_index(
    preprocessed: Path,
    *,
    subject: str,
    submission_type: str,
    extensions: set[str],
    k: int,
    window: int,
    min_tokens: int,
) -> dict[str, dict[str, dict[int, set[str]]]]:
    students: dict[str, dict[str, dict[int, set[str]]]] = {}
    for folder in sorted(preprocessed.iterdir()):
        if not folder.is_dir() or folder.name in SKIP_DIRS or folder.name.startswith("_"):
            continue
        std_id = std_id_from_folder(folder.name, subject, submission_type)
        per_language: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))

        for path in iter_files(folder, extensions):
            lang = LANG_BY_EXT.get(path.suffix.lower())
            if not lang:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            tokens = tokenize(text, lang)
            if len(tokens) < min_tokens:
                continue
            relative = str(path.relative_to(folder))
            for value in fingerprints(tokens, k, window):
                per_language[lang][value].add(relative)

        if per_language:
            students[std_id] = {lang: dict(table) for lang, table in per_language.items()}
    return students


def compare(students: dict, threshold: float, containment_threshold: float) -> list[dict]:
    ids = sorted(students)
    flagged: list[dict] = []

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            left_id, right_id = ids[i], ids[j]
            best: dict | None = None

            for lang in set(students[left_id]) & set(students[right_id]):
                left, right = students[left_id][lang], students[right_id][lang]
                shared = set(left) & set(right)
                if not shared:
                    continue
                union = len(set(left) | set(right))
                similarity = len(shared) / union if union else 0.0
                containment = len(shared) / min(len(left), len(right))

                pair_counts: dict[tuple[str, str], int] = defaultdict(int)
                for value in shared:
                    for left_file in left[value]:
                        for right_file in right[value]:
                            pair_counts[(left_file, right_file)] += 1
                evidence = None
                if pair_counts:
                    evidence = max(pair_counts.items(), key=lambda item: item[1])

                candidate = {
                    "lang": lang,
                    "similarity": round(similarity, 3),
                    "containment": round(containment, 3),
                    "shared": len(shared),
                    "evidence": (
                        {
                            "file_a": evidence[0][0],
                            "file_b": evidence[0][1],
                            "shared_fp": evidence[1],
                        }
                        if evidence
                        else None
                    ),
                }
                if best is None or candidate["similarity"] > best["similarity"]:
                    best = candidate

            if best and (
                best["similarity"] >= threshold or best["containment"] >= containment_threshold
            ):
                flagged.append({"a": left_id, "b": right_id, **best})

    flagged.sort(key=lambda item: (item["similarity"], item["containment"]), reverse=True)
    return flagged


@dataclass
class Report:
    payload: dict
    text: str


def run(
    *,
    preprocessed: Path,
    subject: str,
    submission_type: str,
    extensions: set[str] | None = None,
    threshold: float = DEFAULTS["threshold"],
    containment: float = DEFAULTS["containment"],
    k: int = DEFAULTS["k"],
    window: int = DEFAULTS["window"],
    min_tokens: int = DEFAULTS["min_tokens"],
) -> Report:
    if not preprocessed.is_dir():
        raise UsageError(f"not a directory: {preprocessed}")

    students = build_index(
        preprocessed,
        subject=subject,
        submission_type=submission_type,
        extensions=extensions or set(LANG_BY_EXT),
        k=k,
        window=window,
        min_tokens=min_tokens,
    )
    pairs = compare(students, threshold, containment)

    payload = {
        "preprocessed": str(preprocessed),
        "params": {
            "k": k,
            "window": window,
            "threshold": threshold,
            "containment": containment,
            "min_tokens": min_tokens,
        },
        "students_indexed": sorted(students),
        "flagged_pairs": pairs,
    }

    lines = [
        "# Similarity report (INSTRUCTOR ONLY)",
        f"preprocessed: {preprocessed}",
        f"students indexed: {len(students)}",
        f"params: k={k} window={window} threshold={threshold} containment={containment}",
        "",
    ]
    if not pairs:
        lines.append(
            "No pairs above threshold. That is not proof of originality — the "
            "thresholds may be too high, or the copying may span languages."
        )
    else:
        lines.append(
            f"Flagged {len(pairs)} pair(s). REVIEW BY HAND — similarity is a signal, not proof, "
            "and must not change anyone's grade on its own.\n"
        )
        for pair in pairs:
            lines.append(
                f"  {pair['a']}  <->  {pair['b']}   sim={pair['similarity']}  "
                f"containment={pair['containment']}  shared={pair['shared']}  [{pair['lang']}]"
            )
            evidence = pair.get("evidence")
            if evidence:
                lines.append(
                    f"      e.g. {evidence['file_a']}  ~  {evidence['file_b']}  "
                    f"({evidence['shared_fp']} shared fingerprints)"
                )

    return Report(payload=payload, text="\n".join(lines) + "\n")


def write(report: Report, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "plagiarism.json"
    text_path = out_dir / "plagiarism_report.txt"
    json_path.write_text(json.dumps(report.payload, indent=2, ensure_ascii=False), encoding="utf-8")
    text_path.write_text(report.text, encoding="utf-8")
    return json_path, text_path

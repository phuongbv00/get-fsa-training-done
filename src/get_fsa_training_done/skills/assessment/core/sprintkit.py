"""The learner-facing sprint pack, derived from the project spec.

Same argument as `emit`: the model authors one artifact — the spec — and
everything a team actually receives is generated from it. Hand-writing the
handout means the calendar in the spec, the checklist the team reads, and the
gates `verify` enforces are three copies of the same facts, and they drift.

So the gate text lives here, in Python, exactly once per language. The spec's
`## Sprint checkpoint` section is generated from it, the handout is generated
from it, and `verify.capstone` checks the spec against the same gate ids.

**Language.** English is the default, and a team that works in another language
should read the handout in it — a checklist nobody reads is not a gate. That
cannot be delegated to the model, though: the moment the pack is translated by
hand it stops being derived, and the drift this module exists to prevent comes
straight back. So each supported language is a `Locale` below, and adding one
means adding a `Locale`, not editing a caller.

The gate **ids** are deliberately language-neutral. `verify.capstone` looks for
`G1`–`G5` and `D01`–`D05`, so a Vietnamese spec passes the same checks an
English one does, and a rubric's caps can name the gate that triggered them
whatever language the handout was printed in.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from .verify.capstone import CHECKPOINT_GATES, DELIVERABLE_NAMES, Sprint, parse_sprints
from .verify.common import CheckResult

#: Everything is due at the end of the sprint's last day.
DEADLINE_TIME = "23:59"

DEFAULT_LANGUAGE = "en"

#: Columns of the frozen backlog snapshot. Kept English in every locale: they
#: are the header of a CSV an instructor reads ten of per sprint, and they are
#: the names the rubric's G1 criterion refers to.
BACKLOG_COLUMNS = (
    "User Story",
    "Task",
    "Assignee",
    "Estimate (h)",
    "Status",
    "Note",
)

BACKLOG_STATUSES = ("Todo", "Doing", "Done", "Carried over")

BACKLOG_EXAMPLE_ROWS = (
    (
        "US-01 Patient books an appointment",
        "T-011 Time-slot picker",
        "PhuongBV3",
        "6",
        "Done",
        "",
    ),
    (
        "US-01 Patient books an appointment",
        "T-012 Double-booking check API",
        "LinhTT127",
        "8",
        "Carried over",
        "Added 2026-09-08",
    ),
)


@dataclass(frozen=True)
class Gate:
    id: str
    title: str
    body: str
    #: Tick-box lines for the per-sprint checklist. `{n}` is the sprint number.
    checklist: tuple[str, ...]


@dataclass(frozen=True)
class Locale:
    """One language's copy of the pack.

    The prose lives in whole templates rather than field-per-phrase, so a
    translator reads a document instead of a phrasebook and cannot leave half a
    sentence in the wrong language.
    """

    code: str
    gates: tuple[Gate, ...]
    #: `{name_suffix} {code_line} {schedule} {gate_count} {gates} {checklist}`
    guide: str
    #: `{gate_count} {deadline} {count} {gates}`
    checkpoint: str
    review: str
    #: `{n} {end} {deadline}`
    sprint_heading: str


GATES_EN: tuple[Gate, ...] = (
    Gate(
        id="G1",
        title="Backlog freeze",
        body="""Freeze the backlog **before** the sprint starts and export it as
`backlog_sprint<N>_open.csv`; export it again at the end as
`backlog_sprint<N>_close.csv`. Use `backlog_template.csv` for the columns.

- Every task has **exactly one** Assignee and an Estimate. A task nobody owns is
  a task nobody planned, and it counts as missing.
- Tasks added after the freeze are allowed, but must carry
  `Added <YYYY-MM-DD>` in the `Note` column and appear in the G4 record as a
  scope change.
- The `Status` column accepts only: {statuses}.""",
        checklist=(
            "`backlog_sprint{n}_open.csv` exported before the sprint started",
            "`backlog_sprint{n}_close.csv` exported at the end of the sprint",
            "Every task has an Assignee and an Estimate",
            "Post-freeze tasks carry `Added <date>` in the Note column",
        ),
    ),
    Gate(
        id="G2",
        title="Code tag",
        body="""Create an annotated tag on the default branch and push it before the
deadline:

```bash
git tag -a sprint-<N> -m "Sprint <N>: <scope summary>"
git push origin sprint-<N>
```

- **The tag date is the proof you delivered on time.** A tag created after the
  deadline is late, however long ago the code was written.
- Do not upload source code to Drive. The tag is the code submission.
- The repository must be reachable by the instructor's account when it is
  marked.""",
        checklist=(
            "`git tag -a sprint-{n}` created on the default branch",
            "`git push origin sprint-{n}` done, and the tag shows on the repository page",
            "The instructor can open the repository",
        ),
    ),
    Gate(
        id="G3",
        title="Submission folder",
        body="""Submit to this Google Drive path, exactly:

`{drive_root}/<TEAM>/Sprint <N>/`

Contents, with these filenames:

| File | From gate |
|---|---|
| `backlog_sprint<N>_open.csv` | G1 |
| `backlog_sprint<N>_close.csv` | G1 |
| `sprint<N>_review.md` | G4 |
| That sprint's deliverable | G5 |

**The Drive upload time is the submission time.** Files edited after the
deadline are not read — what gets marked is what the folder held at {deadline}
on the sprint's last day.""",
        checklist=(
            "Folder `{drive_root}/<TEAM>/Sprint {n}/` created",
            "Every file in the table above is there, named exactly",
            "No source code in the Drive folder",
        ),
    ),
    Gate(
        id="G4",
        title="Sprint review record",
        body="""Write `sprint<N>_review.md` **during the sprint review**, not after.
Use `sprint_review_template.md` for the shape. The record needs a date and every
member's name.

The per-member section is the primary evidence for the individual mark. Name
task ids and the actual code — "helped the team" cannot be graded.""",
        checklist=(
            "`sprint{n}_review.md` has a date and every member's name",
            "The done list reconciles with `backlog_sprint{n}_close.csv`",
            'Scope changes are written out, or "None" is stated',
            "Every member has a contribution line naming task ids",
        ),
    ),
    Gate(
        id="G5",
        title="Sprint deliverable",
        body="""The deliverable that sprint owns, per the sprint schedule above. Each
deliverable's own rules — diagram-as-code, the `docs/` layout, submission format
— are in the brief's Deliverables section and apply here unchanged.""",
        checklist=("Sprint {n}'s deliverable submitted: {deliverables}",),
    ),
)

GUIDE_EN = """# Sprint submission guide{name_suffix}
{code_line}
This document covers **what to submit, where, and by when**. What goes
*inside* each deliverable is in the brief and is not repeated here.

## Sprint schedule

| Sprint | Start | End | Deadline | Deliverables due |
|---|---|---|---|---|
{schedule}

## The {gate_count} gates, every sprint

Missing any gate costs marks — the exact caps are in the rubric your instructor
publishes. A gate is not paperwork: it is dated evidence of what the team did
and who did it, and that is the one thing you cannot reconstruct the night
before the defence.

{gates}
## Per-sprint checklist

{checklist}
## What costs the most marks

- A backlog written after the work, so the open and close snapshots are identical.
- Tasks with no Assignee — there is then nothing to read for the individual mark.
- A tag created after the deadline. On-time code with a late tag is a late submission.
- Uploading a source archive to Drive instead of tagging.
- A review record that says "helped the team" instead of naming task ids.
- Editing Drive files after the deadline. What gets marked is what the folder
  held when time ran out.
"""

CHECKPOINT_EN = """## Sprint checkpoint

At the end of every sprint the team must clear all {gate_count} gates below
before **{deadline} on the sprint's last day** in the `## Sprints` table.
A missed gate is capped under `## 4. Caps and Deductions` in the rubric.

`<N>` is the sprint number, 1 to {count}.

{gates}"""

REVIEW_EN = """# Sprint <N> Review — <TEAM>

> **Date:** <YYYY-MM-DD>
> **Present:** <every member's name>

## Done

<User stories marked Done. Must reconcile with backlog_sprint<N>_close.csv.>

## Not done, and why

<User stories still Todo/Doing, why, and which sprint picks them up.>

## Scope change

<Tasks added after the freeze: who decided, what was traded away. Write "None"
if there were none.>

## Per-member contribution

<One line per member: which task ids, which code. This is the primary evidence
for the individual mark — writing "helped the team" forfeits it.>

- <Name> — <task ids>, <what they built>
- <Name> — <task ids>, <what they built>

## Commitment for next sprint

<The user stories the team takes on for the next sprint.>
"""

GATES_VI: tuple[Gate, ...] = (
    Gate(
        id="G1",
        title="Backlog freeze",
        body="""Chốt backlog **trước** ngày bắt đầu sprint và export ra
`backlog_sprint<N>_open.csv`; export lại lúc kết thúc thành
`backlog_sprint<N>_close.csv`. Dùng `backlog_template.csv` làm mẫu cột.

- Mỗi task có **đúng một** Assignee và một Estimate. Task không có người nhận là
  task chưa được lập kế hoạch, và bị tính là thiếu.
- Task thêm sau khi freeze vẫn được phép, nhưng phải ghi `Added <YYYY-MM-DD>`
  vào cột `Note` và xuất hiện trong biên bản G4 như một scope change.
- Cột `Status` chỉ nhận: {statuses}.""",
        checklist=(
            "`backlog_sprint{n}_open.csv` đã export trước ngày bắt đầu sprint",
            "`backlog_sprint{n}_close.csv` đã export lúc kết thúc sprint",
            "Mọi task đều có Assignee và Estimate",
            "Task thêm sau freeze đã ghi `Added <ngày>` ở cột Note",
        ),
    ),
    Gate(
        id="G2",
        title="Code tag",
        body="""Tạo annotated tag trên nhánh mặc định và push trước hạn:

```bash
git tag -a sprint-<N> -m "Sprint <N>: <tóm tắt phạm vi>"
git push origin sprint-<N>
```

- **Ngày của tag là bằng chứng nộp đúng hạn.** Tag tạo sau hạn là nộp muộn, dù
  code đã viết xong từ trước.
- Không nộp source code lên Drive. Tag chính là bản nộp của code.
- Repository phải truy cập được bằng tài khoản giảng viên tại thời điểm chấm.""",
        checklist=(
            "`git tag -a sprint-{n}` đã tạo trên nhánh mặc định",
            "`git push origin sprint-{n}` đã chạy, tag hiện trên trang repository",
            "Giảng viên truy cập được repository",
        ),
    ),
    Gate(
        id="G3",
        title="Submission folder",
        body="""Nộp vào thư mục Google Drive, đúng đường dẫn:

`{drive_root}/<TEAM>/Sprint <N>/`

Nội dung, đúng tên file:

| File | Từ gate |
|---|---|
| `backlog_sprint<N>_open.csv` | G1 |
| `backlog_sprint<N>_close.csv` | G1 |
| `sprint<N>_review.md` | G4 |
| Deliverable của sprint đó | G5 |

**Thời điểm upload trên Drive là thời điểm nộp.** File sửa sau hạn không được
đọc — bản được chấm là bản có trong thư mục lúc {deadline} ngày kết thúc
sprint.""",
        checklist=(
            "Thư mục `{drive_root}/<TEAM>/Sprint {n}/` đã tạo",
            "Đủ file trong bảng trên, tên đúng từng ký tự",
            "Không có source code trong thư mục Drive",
        ),
    ),
    Gate(
        id="G4",
        title="Sprint review record",
        body="""Viết `sprint<N>_review.md` **trong buổi sprint review**, không viết sau.
Dùng `sprint_review_template.md` làm khung. Biên bản phải có ngày và đủ tên
thành viên.

Phần đóng góp từng thành viên là bằng chứng chính để chấm điểm cá nhân. Viết
task id và phần code cụ thể — "hỗ trợ nhóm" không chấm được.""",
        checklist=(
            "`sprint{n}_review.md` có ngày và đủ tên thành viên",
            "Mục đã xong khớp với `backlog_sprint{n}_close.csv`",
            'Scope change được ghi rõ, hoặc ghi "Không có"',
            "Mỗi thành viên có một dòng đóng góp nêu task id",
        ),
    ),
    Gate(
        id="G5",
        title="Sprint deliverable",
        body="""Deliverable mà sprint đó chịu trách nhiệm, theo bảng lịch sprint ở
trên. Quy tắc của từng deliverable — diagram-as-code, bố cục `docs/`, định dạng
nộp — nằm ở mục Deliverables của đề bài và áp dụng nguyên vẹn ở đây.""",
        checklist=("Deliverable của sprint {n} đã nộp: {deliverables}",),
    ),
)

GUIDE_VI = """# Hướng dẫn nộp bài theo sprint{name_suffix}
{code_line}
Tài liệu này nói **nộp cái gì, nộp ở đâu, hạn lúc nào**. Nội dung bên trong từng
deliverable nằm ở đề bài, không lặp lại ở đây.

## Lịch sprint

| Sprint | Bắt đầu | Kết thúc | Hạn nộp | Deliverable chốt |
|---|---|---|---|---|
{schedule}

## {gate_count} gate phải qua ở mỗi sprint

Thiếu bất kỳ gate nào cũng bị trừ điểm — mức trừ cụ thể ở rubric giảng viên công
bố. Gate không phải thủ tục: nó là bằng chứng có ngày tháng cho việc nhóm đã làm
gì và ai đã làm, thứ duy nhất không thể dựng lại vào đêm trước buổi bảo vệ.

{gates}
## Checklist từng sprint

{checklist}
## Những lỗi mất điểm nhiều nhất

- Viết backlog sau khi làm xong, nên hai snapshot open và close giống hệt nhau.
- Task không có Assignee — điểm cá nhân không có gì để đọc.
- Tag tạo sau hạn. Code viết đúng hạn nhưng tag muộn vẫn là nộp muộn.
- Nộp file nén source code lên Drive thay vì tag.
- Biên bản ghi "hỗ trợ nhóm" thay vì nêu task id.
- Sửa file trên Drive sau hạn. Bản được chấm là bản có trong thư mục lúc hết hạn.
"""

CHECKPOINT_VI = """## Sprint checkpoint

Cuối mỗi sprint, nhóm phải qua đủ {gate_count} gate dưới đây trước
**{deadline} ngày kết thúc sprint** trong bảng `## Sprints`. Gate nào thiếu sẽ
bị áp cap ở mục `## 4. Caps and Deductions` của rubric.

`<N>` là số sprint, từ 1 đến {count}.

{gates}"""

REVIEW_VI = """# Sprint <N> Review — <TÊN NHÓM>

> **Ngày:** <YYYY-MM-DD>
> **Có mặt:** <tên tất cả thành viên>

## Đã xong

<User story đã Done. Phải khớp với backlog_sprint<N>_close.csv.>

## Chưa xong và lý do

<User story còn Todo/Doing, lý do, và sprint nào sẽ nhận lại.>

## Scope change

<Task thêm sau khi freeze: ai quyết định, đánh đổi cái gì. Ghi "Không có" nếu
không có.>

## Đóng góp từng thành viên

<Mỗi thành viên một dòng: task id nào, phần code nào. Đây là bằng chứng chính để
chấm điểm cá nhân — viết "hỗ trợ nhóm" là bỏ điểm.>

- <Tên> — <task id>, <phần đã làm>
- <Tên> — <task id>, <phần đã làm>

## Cam kết sprint sau

<Những user story nhóm nhận cho sprint kế tiếp.>
"""

LOCALES: dict[str, Locale] = {
    "en": Locale(
        code="en",
        gates=GATES_EN,
        guide=GUIDE_EN,
        checkpoint=CHECKPOINT_EN,
        review=REVIEW_EN,
        sprint_heading="### Sprint {n} — due {end} {deadline}",
    ),
    "vi": Locale(
        code="vi",
        gates=GATES_VI,
        guide=GUIDE_VI,
        checkpoint=CHECKPOINT_VI,
        review=REVIEW_VI,
        sprint_heading="### Sprint {n} — hạn {end} {deadline}",
    ),
}

LANGUAGES = tuple(LOCALES)


def locale_for(code: str) -> Locale:
    try:
        return LOCALES[code]
    except KeyError:
        raise UsageError(
            f"unsupported --lang {code!r}; the sprint pack is generated, not translated "
            f"by hand, so it exists in {', '.join(LANGUAGES)} only. Adding a language "
            "means adding a Locale in core/sprintkit.py"
        ) from None


@dataclass(frozen=True)
class Project:
    name: str
    code: str
    sprints: tuple[Sprint, ...]


_TITLE = re.compile(r"^#\s+Project Spec\s*[-–—]\s*(.+?)\s*$", re.MULTILINE)
_CODE = re.compile(r"^>\s*\*\*Code:\*\*\s*(.+?)\s*$", re.MULTILINE)


def read_project(spec_path: Path) -> Project:
    """Parse the spec, refusing to generate a handout from a calendar that fails
    verification — the two must not disagree about when anything is due."""
    if not spec_path.exists():
        raise UsageError(f"missing project spec: {spec_path}")
    text = spec_path.read_text(encoding="utf-8")

    result = CheckResult()
    sprints = parse_sprints(text, result)
    if result.errors:
        joined = "\n  - ".join(result.errors)
        raise UsageError(
            f"{spec_path} has an unusable sprint calendar:\n  - {joined}\n"
            "Fix the spec's '## Sprints' table, then re-run."
        )
    if any(sprint.start is None or sprint.end is None for sprint in sprints):
        raise UsageError(f"{spec_path}: every sprint needs a start and an end date")

    title = _TITLE.search(text)
    code = _CODE.search(text)
    return Project(
        name=title.group(1) if title else "",
        code=code.group(1) if code else "",
        sprints=tuple(sprints),
    )


def _deliverables(sprint: Sprint) -> str:
    return ", ".join(f"{d} {DELIVERABLE_NAMES.get(d, '')}".strip() for d in sprint.deliverables)


def _gate_body(gate: Gate, drive_root: str) -> str:
    return gate.body.format(
        statuses=", ".join(f"`{status}`" for status in BACKLOG_STATUSES),
        drive_root=drive_root,
        deadline=DEADLINE_TIME,
    )


def _gate_blocks(locale: Locale, drive_root: str, separator: str) -> str:
    return "\n".join(
        f"### {gate.id}{separator}{gate.title}\n\n{_gate_body(gate, drive_root)}\n"
        for gate in locale.gates
    )


def checkpoint_section(project: Project, drive_root: str, locale: Locale) -> str:
    """The `## Sprint checkpoint` block that belongs in the spec."""
    body = locale.checkpoint.format(
        gate_count=len(locale.gates),
        deadline=DEADLINE_TIME,
        count=len(project.sprints),
        gates=_gate_blocks(locale, drive_root, " - "),
    )
    return body.rstrip() + "\n"


def _schedule_rows(project: Project) -> str:
    return "\n".join(
        f"| {sprint.number} | {sprint.start} | {sprint.end} | "
        f"{sprint.end} {DEADLINE_TIME} | {_deliverables(sprint) or '—'} |"
        for sprint in project.sprints
    )


def _checklist_blocks(project: Project, drive_root: str, locale: Locale) -> str:
    blocks = []
    for sprint in project.sprints:
        lines = [
            locale.sprint_heading.format(n=sprint.number, end=sprint.end, deadline=DEADLINE_TIME),
            "",
        ]
        for gate in locale.gates:
            for item in gate.checklist:
                filled = item.format(
                    n=sprint.number,
                    drive_root=drive_root,
                    deliverables=_deliverables(sprint) or "—",
                )
                lines.append(f"- [ ] **{gate.id}** {filled}")
        blocks.append("\n".join(lines) + "\n")
    return "\n".join(blocks)


def handout(project: Project, drive_root: str, locale: Locale) -> str:
    """The single document a team receives: schedule, gates, per-sprint checklist."""
    body = locale.guide.format(
        name_suffix=f" - {project.name}" if project.name else "",
        code_line=f"\n> **Code:** {project.code}\n" if project.code else "",
        schedule=_schedule_rows(project),
        gate_count=len(locale.gates),
        gates=_gate_blocks(locale, drive_root, " — "),
        checklist=_checklist_blocks(project, drive_root, locale),
    )
    return body.rstrip() + "\n"


def write_backlog_template(path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(BACKLOG_COLUMNS)
        writer.writerows(BACKLOG_EXAMPLE_ROWS)


def write_kit(project: Project, out_dir: Path, drive_root: str, locale: Locale) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    guide = out_dir / "SUBMISSION_GUIDE.md"
    guide.write_text(handout(project, drive_root, locale), encoding="utf-8")
    written.append(guide)

    review = out_dir / "sprint_review_template.md"
    review.write_text(locale.review, encoding="utf-8")
    written.append(review)

    backlog = out_dir / "backlog_template.csv"
    write_backlog_template(backlog)
    written.append(backlog)

    section = out_dir / "spec_sprint_checkpoint.md"
    section.write_text(checkpoint_section(project, drive_root, locale), encoding="utf-8")
    written.append(section)

    return written


_CHECKPOINT_HEADING = re.compile(r"^##\s+Sprint checkpoint\s*$", re.MULTILINE)


def update_spec(spec_path: Path, project: Project, drive_root: str, locale: Locale) -> None:
    """Replace the spec's `## Sprint checkpoint` section with the generated one."""
    text = spec_path.read_text(encoding="utf-8")
    heading = _CHECKPOINT_HEADING.search(text)
    if not heading:
        raise UsageError(
            f"{spec_path} has no '## Sprint checkpoint' heading to replace; add the "
            "heading where the section belongs, then re-run with --update-spec"
        )
    following = re.search(r"^##\s", text[heading.end() :], re.MULTILINE)
    end = heading.end() + following.start() if following else len(text)
    replacement = checkpoint_section(project, drive_root, locale)
    spec_path.write_text(
        text[: heading.start()] + replacement + "\n" + text[end:], encoding="utf-8"
    )


def gate_ids(locale: Locale | None = None) -> tuple[str, ...]:
    return tuple(gate.id for gate in (locale or LOCALES[DEFAULT_LANGUAGE]).gates)


#: Every locale and the verifier must agree on the gate list, or a team can pass
#: every gate it was told about and still fail verification.
for _locale in LOCALES.values():
    assert gate_ids(_locale) == tuple(CHECKPOINT_GATES), (
        f"{_locale.code} gates drifted from verify.capstone"
    )

---
name: get-fsa-training-done
description: Get FSA training done end to end. Program - design and verify a training programme (curriculum, schedules, syllabi, session plans) and export the FPT vendor workbooks. Material - write and check the lecture notes, handbooks and lab guides a session plan calls for. Assessment - design quizzes, assignments, theory and practice exams and capstones (briefs, rubrics, Blooket and Coderbyte imports), and grade submissions, quiz reports and cheat checks. Use when asked to "thiết kế chương trình đào tạo", "viết syllabus", "xuất file Excel", "viết bài giảng", "soạn tài liệu", "viết lab", "tạo quiz", "ra đề", "tạo assignment", "chấm bài", "chấm điểm", "design a training programme", "write a lecture note", "design an assessment", or "grade submissions".
---

# Get FSA training done

One skill, three features. **Program** declares what a training programme
contains, **material** writes the teaching documents its sessions name, and
**assessment** writes and grades the marked work. A topic's ScheduleDetail CSV
binds them: a session row names the file that serves it, and the feature that
owns that kind of file produces it.

| Feature | Owns |
|---|---|
| program | modules, schedules, syllabi, session plans, vendor workbooks |
| material | lecture notes, handbooks, appendices, lab guides |
| assessment | questions, briefs, rubrics, import files, grading |

No feature writes another's artifact. When a finding is really about someone
else's file, name the feature that owns it.

## This skill is stateless

It knows nothing about the directory structure it was installed into and
assumes nothing about the project around it. **Every path it touches is one the
user gave it.**

> **Do not list, glob, read, or run anything until every required Step 0 value
> has a confirmed value.** The only file you may read before that point is one
> the user has just named in this conversation. Do not infer values from the
> working directory, from folder names, or from files you happen to notice.

The one path you legitimately know is `SKILL_DIR` — the directory containing the
`SKILL.md` you are reading right now. Reference files below are relative to it.

## Resolving the CLI

Do this once per session, before the first command, and call the result `FSA`.

1. Read `.get-fsa-training-done-install.json` next to this `SKILL.md`; use its
   `cli.invocation` array, adding its `pythonpath` to `PYTHONPATH`.
2. Otherwise try `get-fsa-training-done --version` on `PATH`.
3. Otherwise stop and ask the user to run `pip install get-fsa-training-done` or
   `npm install -g get-fsa-training-done`. Do not improvise a path to a script.

A receipt written on another machine names an interpreter that does not exist
here; when its invocation fails to run, fall through to option 2. If option 2
reports a version different from the `VERSION` file beside this `SKILL.md`, say
so — payload and CLI ship in lockstep, and an older CLI left on `PATH` is not
the one these workflows were written against.

`FSA` is the **bare CLI**, with no subcommand attached. Each feature's work runs
under its namespace — `FSA program verify`, `FSA material verify`,
`FSA assessment render` — while the lifecycle commands take no namespace:
`FSA doctor`, `FSA status`, `FSA update`. A worker verb written without its
namespace resolves to nothing.

## Step 1 — Route

Decide the feature from the request, then read that feature's overview — it
holds the Step 0 inputs, the commands, and the standing rules — and then
**exactly one** workflow file. Do not read the others.

### Program — `references/program/overview.md`

| Intent | Workflow |
|---|---|
| author a programme and its schedules | `references/program/workflows/author/program.md` |
| author a topic's syllabus and session plan | `references/program/workflows/author/topic.md` |
| change a session plan and re-derive what follows | `references/program/workflows/author/revise.md` |
| read a verification report | `references/program/workflows/verify/report.md` |
| produce the vendor workbook | `references/program/workflows/export/workbooks.md` |

### Material — `references/material/overview.md`

| Intent | Workflow |
|---|---|
| write a lecture note | `references/material/workflows/author/lecture.md` |
| write a lab guide | `references/material/workflows/author/lab.md` |
| write the module handbook | `references/material/workflows/author/handbook.md` |
| write or refresh the module appendix | `references/material/workflows/author/appendix.md` |
| read a verification report | `references/material/workflows/verify/report.md` |
| find out what material is missing | `references/material/workflows/coverage/gaps.md` |

### Assessment — `references/assessment/overview.md`

| Intent | Type | Workflow | Verifier prompt |
|---|---|---|---|
| design | `quiz` | `references/assessment/workflows/design/quiz.md` | `references/assessment/verifiers/quiz.md` |
| design | `short_assignment` | `references/assessment/workflows/design/short_assignment.md` | `references/assessment/verifiers/short_assignment.md` |
| design | `long_assignment` | `references/assessment/workflows/design/long_assignment.md` | `references/assessment/verifiers/long_assignment.md` |
| design | `theory_exam` | `references/assessment/workflows/design/theory_exam.md` | `references/assessment/verifiers/theory_exam.md` |
| design | `practice_exam` | `references/assessment/workflows/design/practice_exam.md` | `references/assessment/verifiers/practice_exam.md` |
| design | `capstone_project` | `references/assessment/workflows/design/capstone_project.md` | `references/assessment/verifiers/capstone_project.md` |
| grade | assignments and exams | `references/assessment/workflows/grade/submissions.md` | — |
| grade | quiz report | `references/assessment/workflows/grade/quiz_report.md` | — |
| grade | copying / AI authorship | `references/assessment/workflows/grade/cheat_check.md` | — |

## Step 2 — Report back

Each feature's overview says what its report contains. In every case: list
every file written with its full path, say which are learner-facing, and give
the `FSA <feature> verify` result. Report measurements, not impressions.

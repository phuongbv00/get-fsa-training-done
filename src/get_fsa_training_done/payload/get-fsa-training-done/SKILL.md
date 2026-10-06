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

Decide the feature from the request, then read that feature's overview — its
naming, language and standing rules — and then **one route**:

- a **workflow** when the user wants the whole job ("ra đề practice exam",
  "chấm bài exam"). A workflow is an ordered list of tasks; read each task file
  when you reach it.
- a **task** when the user wants one step ("render lại PDF", "thêm bản tiếng
  Việt", "gộp điểm thi lại"). A task lists its own inputs and runs on its own.

Do not read routes you are not taking.

### Program — `references/program/overview.md`

| Intent | Workflow |
|---|---|
| author a programme and its schedules | `references/program/workflows/author/program.md` |
| author a topic's syllabus and session plan | `references/program/workflows/author/topic.md` |
| change a session plan and re-derive what follows | `references/program/workflows/author/revise.md` |
| read a verification report | `references/program/workflows/verify/report.md` |
| produce the vendor workbook | `references/program/workflows/export/workbooks.md` |

### Material — `references/material/overview.md`

| Workflow | File |
|---|---|
| all the material a module's plan asks for | `references/material/workflows/module_pack.md` |
| fill what the plan asks for and the folder lacks | `references/material/workflows/fill_gaps.md` |

| Task | File |
|---|---|
| write a lecture note | `references/material/tasks/write_lecture.md` |
| write a lab guide | `references/material/tasks/write_lab.md` |
| write a group lab's worksheet | `references/material/tasks/write_worksheet.md` |
| write the module handbook | `references/material/tasks/write_handbook.md` |
| write or refresh the module appendix | `references/material/tasks/derive_appendix.md` |
| find out what material is missing | `references/material/tasks/coverage.md` |
| verify material, or read a verification report | `references/material/tasks/verify.md` |
| review material before it is published | `references/material/tasks/review_for_trainee.md` |

### Assessment — `references/assessment/overview.md`

| Workflow | Type | File | Verifier prompt |
|---|---|---|---|
| design | `quiz` (multiple choice or written) | `references/assessment/workflows/design/quiz.md` | `references/assessment/verifiers/quiz.md` |
| design | `short_assignment` | `references/assessment/workflows/design/short_assignment.md` | `references/assessment/verifiers/short_assignment.md` |
| design | `long_assignment` | `references/assessment/workflows/design/long_assignment.md` | `references/assessment/verifiers/long_assignment.md` |
| design | `theory_exam` (written or multiple choice) | `references/assessment/workflows/design/theory_exam.md` | `references/assessment/verifiers/theory_exam.md` |
| design | `practice_exam` | `references/assessment/workflows/design/practice_exam.md` | `references/assessment/verifiers/practice_exam.md` |
| design | `capstone_project` | `references/assessment/workflows/design/capstone_project.md` | `references/assessment/verifiers/capstone_project.md` |
| grade | assignments and exams | `references/assessment/workflows/grade/submissions.md` | — |
| grade | a retake, merged with the first attempt | `references/assessment/workflows/grade/retake.md` | — |
| grade | quiz scores | `references/assessment/workflows/grade/quiz_report.md` | — |
| grade | copying / AI authorship | `references/assessment/workflows/grade/cheat_check.md` | — |

| Task | File |
|---|---|
| plan an assessment and confirm it | `references/assessment/tasks/design/plan_scope.md` |
| write or revise a brief | `references/assessment/tasks/design/write_brief.md` |
| write or revise a rubric | `references/assessment/tasks/design/write_rubric.md` |
| write multiple-choice questions | `references/assessment/tasks/design/author_mcq.md` |
| write open-ended or interview questions | `references/assessment/tasks/design/author_oe_questions.md` |
| write an answer template or worksheet | `references/assessment/tasks/design/write_answer_template.md` |
| build supplied files: seed data, a git repo, a starter, a mock API | `references/assessment/tasks/design/build_fixtures.md` |
| emit Blooket or Coderbyte import files | `references/assessment/tasks/design/emit_imports.md` |
| render a brief to PDF | `references/assessment/tasks/design/render_pdf.md` |
| verify an assessment | `references/assessment/tasks/design/verify.md` |
| preprocess submissions | `references/assessment/tasks/grade/preprocess.md` |
| plan grading batches | `references/assessment/tasks/grade/plan_batches.md` |
| score submissions against a rubric | `references/assessment/tasks/grade/score_submissions.md` |
| aggregate score sheets into a grade CSV | `references/assessment/tasks/grade/aggregate.md` |
| merge a retake with the first attempt | `references/assessment/tasks/grade/merge_retake.md` |
| score a quiz report or Blooket leaderboard | `references/assessment/tasks/grade/score_quiz.md` |
| put several quizzes in one table | `references/assessment/tasks/grade/merge_quizzes.md` |
| write a short remark per trainee | `references/assessment/tasks/grade/learner_remarks.md` |
| check similarity between submissions | `references/assessment/tasks/grade/similarity.md` |
| collect AI-authorship signals | `references/assessment/tasks/grade/ai_signals.md` |

### Common — any feature

| Task | File |
|---|---|
| add a Vietnamese version of a finished file | `references/common/tasks/translate_vn.md` |
| run SQL, unit tests or a mock API's tests in Docker | `references/common/tasks/run_in_sandbox.md` |

Writing style for every feature: `references/common/style.md`; Vietnamese:
`references/common/language_vn.md`.

## Step 2 — Report back

Each feature's overview says what its report contains. In every case: list
every file written with its full path, say which are learner-facing, and give
the `FSA <feature> verify` result. Report measurements, not impressions.

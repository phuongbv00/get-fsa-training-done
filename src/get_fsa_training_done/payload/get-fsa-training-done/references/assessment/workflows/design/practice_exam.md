# Workflow — practice exam

A timed build, sat in one sitting with no internet and no AI. Those conditions
are announced outside the paper, never printed in it, but the design assumes
them.

**Produces:** `<stem>.md`, `<stem>_rubric.md`, `<stem>.pdf`, and any supplied
files and worksheets.

| Step | Task | For a practice exam |
|---|---|---|
| 1 | `references/assessment/tasks/design/plan_scope.md` | read what the labs and assignments drilled; pick a fresh domain; score target and profile estimate |
| 2 | `references/assessment/tasks/design/write_brief.md` | `Code: <LEVEL>_<SUBJ>_PE_<seq>`, wall-clock Duration; the 80/20 rule; feasibility, below |
| 3 | `references/assessment/tasks/design/write_rubric.md` | caps for missing foundations; state the 80/20 line |
| 4 | `references/assessment/tasks/design/write_answer_template.md` | when a task's output is writing or a table: a worksheet with the tables drawn |
| 5 | `references/assessment/tasks/design/build_fixtures.md` | seed data and its test, a git repository, a starter — each proven in the sandbox; a reference solution timed against the duration |
| 6 | `references/assessment/tasks/design/render_pdf.md` | **binding** budget: 2 A4 pages per hour |
| 7 | `references/assessment/tasks/design/verify.md` | `--type practice_exam`; verifier `references/assessment/verifiers/practice_exam.md`, which asks for a per-task minute budget |
| 8 | `references/common/tasks/translate_vn.md` | only on request: brief and worksheets, same page budget |

## What is particular to a practice exam

**Feasibility is the design problem.** Everything asked for must be buildable,
by this level of candidate, in the stated time, from memory, on a machine with
no scaffolding beyond what is supplied. Budget each task in minutes and check
they sum to well under the duration: reading, thinking, setting up and checking
come out of the same time as building. When it does not fit, cut a whole task
rather than thinning every task.

**Familiar shape, new domain.** A trainee who did the assignment seriously
should recognise every kind of task; only the domain and the details are new.

**Bullets first.** There is no time to parse prose under exam conditions. One
paragraph per task, at most, for the rule that carries its difficulty.

**Supply what is not being tested.** Seed data when the task is the queries, a
repository with its history when the task is resolving a conflict, tables
already drawn when the task is the analysis. What is supplied is cited inside
the task that uses it.

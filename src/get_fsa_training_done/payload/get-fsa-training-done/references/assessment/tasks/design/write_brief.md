# Task — Write the brief

The learner-facing specification of an assignment or exam. It says what to
build or answer and to what standard, and nothing about how it will be graded.

## Inputs

| Input | Notes |
|---|---|
| the confirmed plan | from `references/assessment/tasks/design/plan_scope.md` |
| the type's parameters | from its workflow: code abbreviation, page budget, task count |

## Produces

`<stem>.md`, learner-facing.

## Steps

### 1. Read the shape

- `references/assessment/examples/brief_example.md` — the brief to imitate.
- `references/assessment/levels.md` — task count, scope, and whether the brief
  may name mechanisms.
- `references/common/style.md` — every rule there applies.

### 2. Write it — exactly three sections

```markdown
# <Type> - <Name>

> **Code:** <LEVEL>_<SUBJ>_<ABBR>_<seq>
> **Level:** <LEVEL>
> **Duration:** <duration>
> **Topics:** <topic> | <topic> | <topic>

---

## 1. Problem Statement

## 2. Tasks

### Task 1 - <name> (<weight>%)

## 3. Deliverables
```

No Prerequisites, no global Constraints, no rules section. A constraint goes in
the task it constrains, where the trainee reads it at the moment it matters.
The banner carries only Code, Level, Duration and Topics.

**Problem Statement.** Under half a page. One or two sentences of business
setting, one clause naming the technical shape ("a REST API over a relational
database"), then the defining rules as **bullets**. Field lists, endpoint tables
and status codes belong in the tasks. When the input is a conversation — a
meeting the trainee must turn into user stories — write it as a transcript of
who said what, and make sure it ends with a decision and holds enough material
for every output the tasks ask for (count it: three user stories need three
clear needs).

**Tasks.** Weights sum to exactly 100%. Lead with bullets stating outcomes;
reserve prose for the single rule that carries the task's difficulty (the
verifier warns past 70 words). A specification task — a feature to query, an
entity to model — gets its own short section with a concrete example, not a
row in a shared table, and every business rule sits with the feature or entity
it governs.

How much to give away depends on the level:

- **Name the mechanism when the mechanism is the objective** — the Stream API, a
  JDBC transaction, a rebase. Naming it *is* the requirement.
- **State the outcome when the mechanism is just good practice**, so the trainee
  has to work out the how:

| Instead of | Write |
|---|---|
| "Use `PreparedStatement` for all user-provided values" | "Must be safe against SQL injection — user input must never change the structure of a SQL statement" |
| "Use try-with-resources for JDBC resources" | "No resource leaks: every connection is released on every path, including when an error occurs midway" |
| "Write the story as: As a ... I want ... so that ..." | "Write the user stories this decision needs" (the three-part form is a rubric criterion) |

The brief states goals; the **standard** a goal is held to — a story's three
parts, a WBS item small enough for one person — lives in the rubric.

**Supplied files.** Cite each one inside the task that uses it, as a quote
right after that task's first requirement line:

```markdown
### Task 1 - Schema from the Specification (20%)

- Write `schema.sql` creating every table the specification below needs.

> `seed.sql` is supplied and loads after your schema. Its column names follow
> the specification; adopt them, or keep your own and amend the supplied file.
```

**Deliverables.** A short `- [ ]` checklist: the archive name from
`references/assessment/grading_contract.md` with the example account
(`<subj>_p_exam_01_PhuongBV3.zip`), the exact files it must contain, and what
must not be in it (`target/`, `node_modules/`, IDE folders, database data
directories, secrets). A written answer is submitted in its supplied template.

### 3. Exams stand alone

- **No reference to a lab or an assignment.** An exam paper is read without the
  course open beside it.
- **A fresh domain.** Never reuse a lab's or an assignment's product — if the
  labs built OrderDesk, the exam is about something else.
- A theory exam is independent of the practice exam: no shared domain, no
  shared scenario.

### 4. The 80/20 rule (exams)

- About **80%** of the marks must be reachable by a trainee who did the labs and
  assignments seriously: the same kinds of task, in a new domain.
- About **20%** discriminates the top band: a harder query, a rebase to keep
  history linear, a WBS, an index choice to justify.
- The brief never calls that part hard, a bonus or optional, and never publishes
  its separate weight. Either give it its own task, or phrase it inside a task
  as **"Encouraged: ..."**. The rubric states the design ceiling.

### 5. What a brief never contains

- A README or write-up about the code. Written work is asked for only when the
  writing *is* the assessed task — an analysis, a set of user stories — and
  then in a supplied template.
- A resource or AI policy. Exam conditions are communicated outside the paper.
- Advice, tips, strategy, or "do Tasks 1-4 first".
- Grading judgement: not "manual loops receive little credit" but "the reports
  must be computed with the Stream API".

## Done when

The brief has the three sections and the four banner lines, its task weights
sum to 100, and a trainee could start every task without asking a question.
`FSA assessment verify` checks the structure in
`references/assessment/tasks/design/verify.md`.

## Hands off to

`references/assessment/tasks/design/write_rubric.md`, then any supplied file in
`references/assessment/tasks/design/build_fixtures.md`.

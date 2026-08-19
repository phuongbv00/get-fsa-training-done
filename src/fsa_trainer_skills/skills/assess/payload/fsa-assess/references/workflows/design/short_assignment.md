# Workflow — short assignment (1–2 days)

Practical work a trainee finishes in one or two sittings. Scoped tightly enough
that the brief itself stays short.

**Produces:** `<stem>.md`, `<stem>_rubric.md`, `<stem>.pdf`

## 1. Read the shape first

- `references/examples/brief_example.md` — the brief to imitate.
- `references/examples/rubric_example.md` — the rubric's tone and depth.
- `references/levels.md` — the confirmed level's Bloom mix, task count, scope,
  rubric posture, and whether you may name mechanisms.
- `references/grading_contract.md` — only if `grade_pipeline` is yes.

## 2. Write the brief — `<stem>.md`

```markdown
# Short Assignment - <Name>

> **Code:** <LEVEL>_<SUBJ>_SA_<seq>
> **Level:** <LEVEL>
> **Duration:** <duration>
> **Topics:** <topic> | <topic> | <topic>

---

## 1. Problem Statement

## 2. Tasks

### Task 1 — <name> (<weight>%)

## 3. Deliverables
```

**Exactly three sections.** No Prerequisites, no global Constraints. A
constraint goes in the task it constrains, where the trainee reads it at the
moment it matters.

**The banner carries only Code, Level, Duration, Topics.** Nothing else.

### Problem Statement

Under half a page. One or two sentences of setting, one clause naming the
technical shape ("a REST API over a relational database"), then the defining
rules as **bullets**. No field lists, no endpoint tables, no status codes — all
of that belongs in the tasks.

### Tasks

Take the task count from the level. Weights sum to exactly 100%.

Lead with bullets stating outcomes. Reserve prose for the single rule that
carries the task's real difficulty; the verifier warns past 70 words.

How much you may give away depends on the level:

- **Name the mechanism when the mechanism is the objective** — the Stream API,
  a JDBC transaction, an interface with two implementations. Here the named API
  *is* what is being assessed, so naming it is the requirement.
- **State the outcome when the mechanism is just good practice** — the trainee
  should have to work out the how.

| Instead of | Write |
|---|---|
| "Use `PreparedStatement` for all user-provided values" | "Must be safe against SQL injection — user input must never change the structure of a SQL statement" |
| "Use try-with-resources for JDBC resources" | "No resource leaks: every connection is released on every path, including when an error occurs midway" |
| "Wrap `SQLException` in `DataAccessException`" | "No JDBC details leaking upward: services must not know which database is in use" |

Business rules — validation ranges, formats, domain constraints — are
specification, not implementation. State those precisely, always.

### Deliverables

A short checklist. What to submit and its exact name, what it must contain, and
what must not be included (`target/`, `node_modules/`, IDE folders, secrets,
build output). Read `references/grading_contract.md` for the archive name.

### Do not

- Require a README or any written deliverable. Assess code, not writing — a
  strong implementation should not lose marks for thin prose. (A README
  belonging to a *provided* artifact is fine; that is a contract they read, not
  one they write.)
- State a resource or AI policy. Exam conditions are communicated elsewhere.
- Give advice, tips, or strategy. No "start with the simplest case", no "if time
  runs short". Weights already say where the marks are.
- Put grading judgement in the brief. Not "manual loops receive little credit"
  but "the reports must be computed with the Stream API".

## 3. Write the rubric — `<stem>_rubric.md`

Six sections, in this order:

```markdown
# Short Assignment Rubric (INSTRUCTOR ONLY) - <Name>

> **Code:** <LEVEL>_<SUBJ>_SA_<seq>
>
> **Learner brief:** [<stem>.md](<stem>.md)
>
> WARNING: **DO NOT distribute this file to learners.**

---

## 1. Grading Principle
## 2. Fixed Task List
## 3. Per-Task Scoring Guide
## 4. Caps and Deductions
## 5. Common point-loss reasons
## 6. Score sheet
```

Task ids and weights **must match the brief exactly**. Sub-criterion tables sum
to exactly 10.0 per task. Every criterion must be settleable by reading files,
by a human or a model, without running anything.

Apply the level's rubric posture — see `references/levels.md`.

## 4. Render, then verify

Render first: the page budget is part of verification and the verifier needs the
PDF.

```bash
FSA render "<output_dir>/<stem>.md"
FSA verify --type short_assignment \
  --brief  "<output_dir>/<stem>.md" \
  --rubric "<output_dir>/<stem>_rubric.md" \
  --pdf    "<output_dir>/<stem>.pdf" \
  --level  "<LEVEL>"
```

If the page budget fails, **cut content** — restated context, paragraphs that
could be bullets, anything the rubric already covers. Re-rendering will not fix
it, and shrinking the font is not an option.

Only render briefs. Never produce a rubric PDF.

## 5. Verifier agent

Run `references/verifiers/short_assignment.md`, giving it the confirmed plan,
the generated paths, the `FSA verify` output, and the topic scope. If it returns
`needs_revision`, revise and re-verify before reporting completion.

# Task — Build the supplied files

Make the files an exam or assignment hands to the trainee, and prove they work
before anyone sits the paper.

## Inputs

| Input | Notes |
|---|---|
| the brief | which files its tasks cite |
| the rubric | every figure it quotes from a supplied file |

## Produces

Beside the brief, named `<stem>_<role>`:

| File | Who sees it | What it is |
|---|---|---|
| `<stem>_seed.sql` | learner | data that loads after the trainee's own schema |
| `<stem>_reference_schema.sql` | instructor | a correct schema the seed is tested against |
| `<stem>_seed_test.sql` | instructor | assertions on every figure the rubric quotes |
| `<stem>_starter/` and `<stem>_starter.zip` | learner | a project to build on |
| `<stem>_repo.zip` | learner | a git repository with real history |
| `<stem>_api/` | learner | a mock API the trainee's client calls, with its tests |

## Steps

1. **Seed data.** Keep it small — enough rows for every query in the brief to
   return a non-trivial, checkable result. Use the column names of the
   specification. Write `seed_test.sql` as `DO` blocks that `RAISE EXCEPTION`
   with the expected and actual value, one per figure the rubric quotes, plus
   the business rules the schema must reject. If the seed is edited later, the
   test is what tells you the rubric is now wrong.
2. **A git repository** is built with real commands and shipped with its `.git`
   — a branch, a conflict waiting to happen, whatever the task needs. Never ship
   a script the trainee runs to create the history: the history is the exam
   material. Set a neutral committer (`Exam Setup <exam@example.invalid>`) and
   include a short `README.md` saying nothing needs installing or running.
3. **A starter project** compiles and its tests pass before anything is added.
   Zip it, and keep the unzipped folder beside the zip for review.
4. **A mock API** is a separate, self-contained server the trainee runs locally,
   so the exam does not depend on any other service. It ships with tests, and
   those tests pass: a broken API in front of a class is a broken exam.
5. Prove each runnable file with `references/common/tasks/run_in_sandbox.md`:
   the reference schema, the seed and its test; the starter's tests; the mock
   API's tests.
6. Keep every instructor file out of what the trainee receives.

## Done when

Every runnable fixture has passed in the sandbox, and the result is reported as
a measurement ("seed_test: 14 checks passed").

## Hands off to

`references/assessment/tasks/design/render_pdf.md`.

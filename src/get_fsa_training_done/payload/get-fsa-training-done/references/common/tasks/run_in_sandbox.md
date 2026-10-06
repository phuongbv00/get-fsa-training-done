# Task — Run in the sandbox

Prove that something runnable does what it should, without running it on this
machine: a seed script and its assertions, a starter project's tests, a mock
API's tests, or a submission's own behaviour during grading.

## Inputs

| Input | Notes |
|---|---|
| `mount` | the directory holding what to run; it is copied, never written |
| `profile` | `postgres` (SQL), `maven` (Java), `python`, `node` |
| command | what to run inside, e.g. `mvn test`, `python -m pytest -q`, `psql -f check.sql` |
| `init` | postgres only: SQL files under `mount`, loaded in order first |

## Produces

An exit code and the command's own output. Nothing is written anywhere.

## Steps

1. Check once per session: `FSA assessment sandbox check`. If Docker is missing,
   say so and stop this task — do not run the code on this machine instead.
2. Run it:

   ```bash
   FSA assessment sandbox run --profile postgres --mount "<dir>" \
     --init schema.sql --init seed.sql -- psql -v ON_ERROR_STOP=1 -f seed_test.sql
   FSA assessment sandbox run --profile maven --mount "<dir>" --prefetch -- mvn test
   FSA assessment sandbox run --profile python --mount "<dir>" --prefetch -- python -m pytest -q
   ```

   `--prefetch` fetches dependencies first, with only the build tool's resolver
   running; the command itself always runs with no network, on a read-only
   filesystem with size-bounded scratch space. Postgres needs no prefetch.
   The prefetch refuses what could run the project's code while online: a
   Python requirement that is not a plain index package (`-e .`, a path, a
   URL), and Maven build extensions. Say so to the user rather than working
   around it.
3. Read the output, not just the exit code. A suite that passes because it ran
   zero tests has proved nothing.

## Done when

The command's result is known and reported as a measurement: "seed_test: 14
checks passed", "mvn test: 23 tests, 0 failures", "exit 124, killed after
600s".

## Hands off to

The task that asked for it. When designing, a failure is a defect in the
supplied file: fix it and run again. When grading, the result is evidence next
to what reading the submission showed, never a replacement for it.

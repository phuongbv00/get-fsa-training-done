# Quiz Rubric (INSTRUCTOR ONLY) - Reviewing a Colleague's Database Report

> **Code:** FR_DBF_Q_02
>
> **Learner brief:** [dbf_quiz_02.md](dbf_quiz_02.md)
>
> WARNING: **DO NOT distribute this file to learners.** This file holds the answers and the exact
> per-criterion grading detail for graders.

---

## 1. Grading Principle

- This is a 30-minute open-ended quiz. Grade the diagnosis, not the length or the prose style.
- A learner who states the mechanism correctly in their own words earns full marks; the notes'
  exact terminology is not required. "Rows with no match are dropped" earns the same as "the
  inner join eliminates them".
- Each task hides a distinct defect. A learner who finds one of two required defects earns only
  that part — do not award the whole criterion for a partially correct diagnosis.
- Rewrites are graded on shape, not on syntax. A query that would not compile but shows the
  right mechanism earns the rewrite marks; a query that compiles but keeps the defect does not.
- Do not run anything. Every answer here is settleable by reading.
- Score each task on a 0-10 raw scale, then apply the task weight.

---

## 2. Fixed Task List

| Task ID | Task | Weighted number | Full-mark evidence |
|---|---|---:|---|
| T1 | Query 1 does not do what it claims | 20% | Both the inner-join exclusion and the group-by-name collapse identified, with a rewrite fixing each |
| T2 | Query 2 returns nothing | 20% | `NOT IN` against a `NULL`-bearing subquery explained as the mechanism, and a rewrite that answers the question |
| T3 | What the two plans establish | 20% | Identical plans read as "the index is not being used", `Rows Removed by Filter` named, the timing difference dismissed as noise |
| T4 | "Safe because it is a single statement" | 20% | Statement atomicity stated correctly, the after-the-fact check shown to be too late, `CHECK` named as the enforcement |
| T5 | A second session | 20% | Non-repeatable read named, a concrete wrong write given, a prevention named with its cost |
| | **Total** | **100%** | |

`final = sum(task_score * weighted_number) / 100`, where each `task_score` is on a 0-10 raw
scale with that task's caps and deductions already folded into it. Nothing is subtracted from
the total afterwards.

---

## 3. Per-Task Scoring Guide

### T1 - Query 1 does not do what it claims (20%)

Expected: the claim is "every customer"; the inner join returns only customers who have at
least one order, so a customer with none disappears entirely. Separately, `GROUP BY c.full_name`
groups by name rather than by identity, so two different customers who share a name are merged
into one row with their orders added together. The fix is a `LEFT JOIN` from `customer`, with
`count(o.order_id)` rather than `count(*)` so a customer with no orders counts 0, grouped by
`c.customer_id`.

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Inner-join exclusion identified | 3.0 | Says customers with zero orders are missing, and attributes it to the join rather than to the `GROUP BY` |
| Group-by-name collapse identified | 3.0 | Says two customers sharing a name merge into one row; grouping must be by the key, not the name |
| Rewrite fixes the join | 1.5 | `LEFT JOIN` from `customer`, with `count(o.order_id)` or an equivalent that yields 0 rather than 1 for a customer with no orders |
| Rewrite fixes the grouping | 1.5 | Groups by `customer_id` (or by key plus name); grouping by name alone is not accepted |
| Changes mapped to reasons | 1.0 | States which change addresses which defect rather than presenting an unexplained query |
| **T1 raw score** | **10.0** | |

> **Note for graders.** `count(*)` with the `LEFT JOIN` is a real error and costs the 1.5 join-rewrite
> points: it returns 1 for a customer with no orders, because the outer join manufactures one
> all-`NULL` row. A learner who spots this specifically has earned the point outright.

### T2 - Query 2 returns nothing (20%)

Expected: `shipment.order_id` holds `NULL` in some rows. `x NOT IN (…)` is false or unknown —
never true — as soon as the list contains a `NULL`, because `x <> NULL` is unknown rather than
true. So the whole result is empty regardless of the data, and an empty result therefore says
nothing about whether orders shipped. Rewrite with `NOT EXISTS` (correlated on `order_id`), or
a `LEFT JOIN … WHERE s.order_id IS NULL`, or by adding `WHERE order_id IS NOT NULL` to the
subquery.

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| `NULL` in the subquery identified | 3.0 | Names the `NULL` rows in `shipment.order_id` as the cause, not a data or join problem |
| Three-valued logic explained | 2.5 | Explains that the comparison is unknown rather than true, so no row can qualify |
| The conclusion rejected | 1.5 | States the empty result is an artifact of the query, so it is not evidence about shipping |
| Correct rewrite | 3.0 | `NOT EXISTS`, anti-join with `IS NULL`, or a `NOT NULL` filter on the subquery — any one is full marks |
| **T2 raw score** | **10.0** | |

### T3 - What the two plans establish (20%)

Expected: the two plans are identical — `Seq Scan`, same cost, same `Rows Removed by Filter`.
That establishes the opposite of the claim: the index is not being used. Plausible causes the
learner may name (any one is enough) — the index is not on `order_id`, `ANALYZE` was not run so
the planner's statistics are stale, or the index was never actually created. The line that
identifies the work worth removing is `Rows Removed by Filter: 99997`: 100 000 rows read to
return 3. The 0.17 ms difference is noise on a single untimed run and carries no weight; the
access method, not the clock, is the evidence.

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Plans read as unchanged | 3.0 | Notices both are `Seq Scan` with identical cost and filter counts, and concludes the index is not in use |
| A plausible cause named | 2.0 | Any one of: wrong column, statistics not refreshed with `ANALYZE`, index not created |
| The right line named | 2.5 | `Rows Removed by Filter: 99997`, with the point that 100 000 rows were read to return 3 |
| Timing dismissed correctly | 2.5 | Calls 0.17 ms noise on one run; says the changed access method is what would constitute evidence |
| **T3 raw score** | **10.0** | |

### T4 - "Safe because it is a single statement" (20%)

Expected: the single `UPDATE` guarantees that the read-and-subtract happens inside the engine
on a locked row, so two concurrent decrements cannot both read the same starting value — there
is no lost update on that row. It guarantees nothing about the *value* being legal. The
application's check runs after the write, and on the path shown the transaction goes on to
`COMMIT` anyway; a check that decides to give up must issue `ROLLBACK`, and even then it is the
wrong place for the rule. The mechanism that actually prevents a negative quantity is a
`CHECK (quantity >= 0)` on the column: the engine refuses the row and the statement fails.

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| What atomicity does give | 3.0 | The decrement is computed by the engine on one row, so concurrent decrements do not overwrite each other |
| Why the later check is too late | 3.0 | The check runs after the write, and the snippet commits regardless; giving up requires `ROLLBACK`, which is absent |
| `CHECK` named as the mechanism | 3.0 | A `CHECK` constraint on `quantity`, enforced by the engine, not by application code |
| Placement reasoning | 1.0 | Says a rule enforced in the application can be bypassed by anything else connecting to the same database |
| **T4 raw score** | **10.0** | |

### T5 - A second session (20%)

Expected: a **non-repeatable read** — the same row read twice in one transaction returns
different values, because the default `READ COMMITTED` lets each statement see other sessions'
committed work. The two reads return the old value and then the new one. A concrete wrong
write: a total computed from the first read and written back, which was never true of the data
at any instant. Prevention: `BEGIN ISOLATION LEVEL REPEATABLE READ`, at the cost of a
serialization failure at commit that the application must be prepared to retry; or doing the
arithmetic in a single statement so there is no gap; or a constraint that makes the bad
outcome impossible to store.

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Anomaly named | 3.0 | "Non-repeatable read", or an unambiguous description of one; "dirty read" and "phantom" are wrong and earn nothing here |
| The two reads described | 1.5 | First read returns the old value, second returns the committed new one, with nothing changed by this transaction |
| A concrete wrong write | 3.0 | A specific derived value — a total, a remaining count — written from the stale first read |
| Prevention named | 1.5 | `REPEATABLE READ`, a single-statement computation, or a constraint |
| Its cost stated | 1.0 | Serialization failure to retry, reduced concurrency, or the equivalent for the option chosen |
| **T5 raw score** | **10.0** | |

---

## 4. Caps and Deductions

Every entry below bounds the **raw 0-10 score of the task it sits under**. The lowest applicable
cap for a task wins, caps are never additive, deductions apply after the cap, and the task score
is floored at 0. The final score is the weighted sum and is never adjusted.

### Every task

| Trigger | Effect |
|---|---:|
| No answers submitted, or answers unrelated to the artifact | cap 1.0 |
| Answers restate the teammate's claims without diagnosing anything | cap 3.0 |
| Answers the learner cannot explain when asked | down to 0 on the task it affects |

### T1 - Query 1 does not do what it claims

| Trigger | Effect |
|---|---:|
| Only one of the two defects found | cap 6.0 |
| Rewrite keeps `count(*)` under a `LEFT JOIN` | -1.5 |

### T2 - Query 2 returns nothing

| Trigger | Effect |
|---|---:|
| Blames the data or a missing join rather than `NULL` semantics | cap 4.0 |
| Accepts the teammate's conclusion that every order shipped | cap 5.0 |

### T3 - What the two plans establish

| Trigger | Effect |
|---|---:|
| Reads the plans as showing an improvement | cap 3.0 |
| Treats the 0.17 ms as the evidence | -2.0 |

### T4 - "Safe because it is a single statement"

| Trigger | Effect |
|---|---:|
| Claims the single statement makes a negative quantity impossible | cap 4.0 |
| Proposes only an application-side fix, with no database constraint | -2.0 |

### T5 - A second session

| Trigger | Effect |
|---|---:|
| Names dirty read or phantom read instead | cap 5.0 |
| No concrete wrong value given, only "the data could be wrong" | -1.5 |

---

## 5. Common point-loss reasons

- **T1:** finding the missing customers but not the merged names, or the reverse; rewriting with
  a `LEFT JOIN` while keeping `count(*)`; grouping by `full_name` in the corrected query too.
- **T2:** attributing the empty result to there being no unshipped orders in the seed data;
  describing `NOT IN` as "slow" rather than as wrong; rewriting with `NOT IN` plus a distinct.
- **T3:** describing the plans as "similar" rather than identical; naming the index as helpful
  because execution time dropped; quoting `cost=` instead of `Rows Removed by Filter`.
- **T4:** conflating "one statement" with "correct value"; proposing that the application read
  the row back and update it again; omitting `ROLLBACK` from the description of giving up.
- **T5:** naming the anomaly correctly but giving no wrong value; proposing `SERIALIZABLE`
  without naming any cost; describing the fix as "use a transaction" when one is already open.

---

## 6. Score sheet

| Task | Score (0-10) | Weight | Weighted |
|---|---:|---:|---:|
| T1 Query 1 does not do what it claims | | 20% | |
| T2 Query 2 returns nothing | | 20% | |
| T3 What the two plans establish | | 20% | |
| T4 "Safe because it is a single statement" | | 20% | |
| T5 A second session | | 20% | |
| **Total** | | **100%** | |

Each task score already carries its own caps and deductions, so the weighted sum is the final
score — there is nothing left to subtract.

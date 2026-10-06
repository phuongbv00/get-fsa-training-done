# Quiz 02 - Reviewing a Colleague's Database Report

> **Code:** FR_DBF_Q_02
> **Level:** FR
> **Duration:** 30 minutes
> **Topics:** SQL correctness | joins and grouping | NULL semantics | query plans and indexing | transactions and isolation

---

## 1. Problem Statement

A teammate sent you the note below about the OrderDesk database and asked you to sign it off.
One thing about the schema matters: the depot logs a parcel before anyone matches it to an
order, so `shipment.order_id` is nullable and some rows hold `NULL`.

> "Query 1 lists every customer with the number of orders they have placed."

```sql
SELECT c.full_name, count(*) AS order_count
FROM   customer c
JOIN   orders o ON o.customer_id = c.customer_id
GROUP  BY c.full_name;
```

> "Query 2 finds orders that never shipped. It returns no rows, so every order has shipped."

```sql
SELECT * FROM orders
WHERE  order_id NOT IN (SELECT order_id FROM shipment);
```

> "I added an index on `order_line` and the page is faster now. Here are the plans."

```text
-- before
Seq Scan on order_line  (cost=0.00..1943.00 rows=12) (actual time=0.021..8.912 rows=3)
  Filter: (order_id = 5001)
  Rows Removed by Filter: 99997

-- after
Seq Scan on order_line  (cost=0.00..1943.00 rows=12) (actual time=0.019..8.740 rows=3)
  Filter: (order_id = 5001)
  Rows Removed by Filter: 99997
```

> "And the stock decrement is safe because it is a single statement."

```sql
BEGIN;
UPDATE order_line SET quantity = quantity - 1 WHERE order_line_id = 1;
-- the application reads the new quantity here and gives up if it went below zero
COMMIT;
```

Answer the five questions below. Two to four sentences each is enough.

---

## 2. Tasks

### Task 1 - Query 1 does not do what it claims (20%)

- Name the two separate reasons it fails the claim.
- Give a corrected query, and say which reason each change fixes.

### Task 2 - Query 2 returns nothing (20%)

- Explain why it returns no rows, and why that is not evidence that every order shipped.
- Rewrite it so it answers the question asked.

### Task 3 - What the two plans establish (20%)

- State what the pair actually shows about the index.
- Name the one line in the "before" plan that identifies the work worth removing.
- The timings differ by 0.17 ms. Say what weight that carries, and why.

### Task 4 - "Safe because it is a single statement" (20%)

- Say precisely what the single `UPDATE` guarantees about the decrement.
- Explain why the application's later check does not stop a negative quantity being stored,
  and name the mechanism that does.

### Task 5 - A second session (20%)

Inside one transaction you read a quantity; a second session updates that row and commits
before your second read.

- Name the anomaly, and say what your two reads return.
- Give one concrete wrong value your transaction could end up writing.
- Name one way to prevent it, and what that choice costs.

---

## 3. Deliverables

- One text or Markdown file with all five answers, numbered Task 1 to Task 5.
- Submit through the channel the trainer names. No runnable code is required.

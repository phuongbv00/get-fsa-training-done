# Querying

> Stack: SQL:2016 · See [00_Study_Guide_Handbook.md](00_Study_Guide_Handbook.md).

## 1. Objectives

After this unit, learners can:

- Join tables and explain which rows a join keeps and which it drops.
- Group rows and aggregate them correctly.
- Read a result set and say whether it answers the question asked.

## 2. Joins

An inner join keeps rows that match on both sides.

```sql
SELECT b.title, a.name
FROM book b
JOIN book_author ba ON ba.book_id = b.id
JOIN author a       ON a.id = ba.author_id;
```

> **Tip.** A book with no author disappears from that result. Use a left join
> when the absence is part of the answer.

## 3. Grouping and Aggregation

```sql
SELECT a.name, COUNT(*) AS titles
FROM author a
JOIN book_author ba ON ba.author_id = a.id
GROUP BY a.name
ORDER BY titles DESC;
```

## 4. Worked Example

```sql
SELECT a.name, COUNT(l.id) AS loans
FROM author a
LEFT JOIN book_author ba ON ba.author_id = a.id
LEFT JOIN loan l         ON l.book_id = ba.book_id
GROUP BY a.name
HAVING COUNT(l.id) > 0;
```

## 5. Common Mistakes

### Counting the wrong thing

`COUNT(*)` after a left join counts the unmatched row too. Count the column
from the joined side instead.

### Filtering in the wrong clause

`WHERE` filters rows before grouping, `HAVING` after. Putting an aggregate in
`WHERE` is an error; putting a row condition in `HAVING` is slower and often
wrong.

## 6. Practical Guidelines

- Say which rows you expect before running the query.
- Alias every table and qualify every column.
- Check a join's row count against the count before it.

## 7. Knowledge Check

1. Which rows does an inner join drop?
2. When does a left join change a `COUNT(*)`?
3. What is the difference between `WHERE` and `HAVING`?
4. Why qualify column names in a multi-table query?
5. How would you check a join has not multiplied rows?

## 8. Further Reading

- [SQL standard overview](https://en.wikipedia.org/wiki/SQL)

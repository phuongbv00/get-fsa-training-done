# Lab 01 — Model and implement the catalogue

**Duration:** 90 min · **Objectives:** DBF-K1, DBF-K2

## Objectives

After this lab, learners can:

- Turn a written domain description into a normalized schema.
- Implement it with keys and constraints, and seed it repeatably.

## Before you start

- A scratch database you can drop and recreate.
- A SQL client connected to it.

## Steps

1. Read the catalogue description and list its entities. You should have three.
2. Draw the relationships between them and mark which side is "many".
3. Write `CREATE TABLE` for each entity, with a primary key on every one. Run
   the script; it should complete with no errors.
4. Add the foreign keys. Re-run from an empty database and confirm it still
   completes in one pass.
5. Write a seed script inserting two authors, three books and one loan. Run it
   twice from a clean database and confirm the row counts match both times.
6. Try to insert a loan referencing a book that does not exist. The database
   should reject it.

## Acceptance

- [ ] The schema script runs from an empty database with no errors.
- [ ] Every table has a primary key, and every relationship a foreign key.
- [ ] The seed script produces the same row counts on a second clean run.
- [ ] A loan referencing a missing book is rejected by the database.

# Relational Modelling

> Stack: SQL:2016 · See [00_Study_Guide_Handbook.md](00_Study_Guide_Handbook.md).

## 1. Objectives

After this unit, learners can:

- Identify the entities and relationships in a written domain description.
- Choose a primary key and justify the choice.
- Normalize a table to third normal form and say what each step removed.

## 2. Entities and Relationships

An entity is a thing the domain talks about; a relationship is how two of them
are connected. The library catalogue has books, authors and loans.

```text
author ──< book ──< loan
```

> **Note.** Read `──<` as "one to many".

## 3. Keys

A primary key identifies a row uniquely and never changes.

```sql
CREATE TABLE book (
    id     BIGINT PRIMARY KEY,
    isbn   CHAR(13) NOT NULL UNIQUE,
    title  TEXT NOT NULL
);
```

Prefer a surrogate key over a natural one when the natural value can change.

## 4. Normalization

Splitting repeated groups out into their own table:

```sql
-- Wrong: an author list crammed into one column
CREATE TABLE book (id BIGINT PRIMARY KEY, authors TEXT);
```

```sql
-- Right: the relationship gets its own table
CREATE TABLE book_author (book_id BIGINT, author_id BIGINT, PRIMARY KEY (book_id, author_id));
```

## 5. Worked Example

```sql
CREATE TABLE author (id BIGINT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE book   (id BIGINT PRIMARY KEY, isbn CHAR(13) NOT NULL UNIQUE, title TEXT NOT NULL);
CREATE TABLE book_author (
    book_id   BIGINT NOT NULL REFERENCES book(id),
    author_id BIGINT NOT NULL REFERENCES author(id),
    PRIMARY KEY (book_id, author_id)
);
```

## 6. Common Problems

### A key that changes

An ISBN is reissued and every referencing row is wrong. Use a surrogate key and
keep the ISBN as a unique column.

### Nullable foreign keys

A loan with no book is not a loan. Make the column `NOT NULL`.

## 7. Practical Guidelines

- Name the entity in the singular: `book`, not `books`.
- Declare every foreign key; the database is where integrity belongs.
- Normalize first, denormalize only with a measurement in hand.

## 8. Knowledge Check

1. What makes a column a candidate key?
2. Why prefer a surrogate key to a natural one?
3. What does third normal form remove that second does not?
4. Where should referential integrity be enforced, and why?
5. When is denormalizing justified?

## 9. Further Reading

- [SQL standard overview](https://en.wikipedia.org/wiki/SQL)

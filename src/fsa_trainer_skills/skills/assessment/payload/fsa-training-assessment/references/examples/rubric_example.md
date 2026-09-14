<!-- Shipped as a worked example. Copied from a real assessment and kept intact so the shape, tone, and depth are the genuine article rather than a sketch. -->

> **This is the rubric to imitate** for tone and depth. The six-section structure it uses is the current one.

# Assignment Rubric (INSTRUCTOR ONLY) - BookNest Library Lending System

> **Code:** H_A_01
>
> WARNING: **DO NOT distribute this file to learners.** This file holds the exact per-criterion grading detail, caps, and deductions for graders.

---

## 1. Grading Principle

- Grade only observable evidence in the submitted files: source code, tests, configuration, README, sample data, and documented outputs.
- Do not award points for checklist claims unless they are backed by verifiable artifacts.
- Review the code and documentation as evidence; do not require executing the project to assign a score.
- Correct mapping and persistence come first. A smaller correct app scores higher than a broad app with broken mappings, unsafe transactions, or unclear query behavior.
- Hibernate/JPA understanding matters. The learner should be able to explain entity state, owning side, generated SQL, transaction boundaries, and fetch strategy decisions.
- Score each task on a 0-10 raw scale, fold that task's caps and deductions into the number, then apply the task weight.

---

## 2. Fixed Task List

| Task ID | Task | Weighted number | Full-mark evidence |
|---|---|---:|---|
| T1 | Hibernate Project Setup & Entity Mapping | 15% | Maven project, dependencies, `persistence.xml`, real DB persistence, explicit entity/table/column/id mappings, consistent access strategy |
| T2 | Relationships & Bean Validation | 20% | Correct relationship mappings, owning side clarity, safe cascade/orphan use, validation annotations, validation flow |
| T3 | Catalog, Member, Lending, and Return Flows | 20% | Catalog/member flows, transactional lending, return flow, availability protection, custom exceptions, service/repository boundaries |
| T4 | JPQL, Named Queries, and Criteria API | 20% | Required JPQL queries, joins, ordering, pagination, named queries, Criteria dynamic search, DTO report projection, safe parameters |
| T5 | Performance Optimization Evidence | 15% | Lazy/eager rationale, N+1 detection and fix, fetch join/batch/DTO use, first-level cache demo, optional second-level cache or justified decision |
| T6 | README and Deliverable Quality | 10% | Build/run docs, README complete, sample data/seed, feature checklist, clean explainable code |
| | **Total** | **100%** | |

`total = sum(task_score * weighted_number) / 100`, where each `task_score` is on a 0-10 raw scale with that task's caps and deductions already folded into it. Nothing is subtracted from the total afterwards.

---

## 3. Per-Task Scoring Guide

### T1 - Hibernate Project Setup & Entity Mapping (15%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Maven setup and dependencies | 1.0 | `pom.xml` declares Java 17+, Hibernate ORM, Jakarta Persistence/JPA, validator, JDBC driver; project uses standard Maven layout |
| `persistence.xml` and database config | 1.5 | Correct `META-INF/persistence.xml`, persistence unit name matches code, DB connection is documented, DB persistence is not in-memory only |
| Entity basics | 1.5 | Required entities are annotated with `@Entity`; each has `@Id`, generated id, protected no-arg constructor, and coherent domain constructors/methods |
| Table and column mapping | 1.5 | Explicit `@Table`, `@Column`, nullability, length, uniqueness, precision where relevant; ISBN/email uniqueness enforced |
| Type mapping quality | 1.0 | Uses `LocalDate`/`LocalDateTime`, `EnumType.STRING`, non-negative numeric fields, no inappropriate `double` for money if money is added |
| Access strategy and encapsulation | 1.0 | Field access used consistently; domain state is protected from invalid public mutation |
| Primary key strategy | 0.5 | `AUTO`, `IDENTITY`, or `SEQUENCE` selected intentionally and explained in README |
| Bootstrap/run reliability | 1.0 | App startup and schema behavior are documented; SQL logging is available for development; `EntityManagerFactory` lifecycle is handled |
| Jakarta/JPA consistency | 1.0 | No mixed `javax.persistence`/`jakarta.persistence` imports; no configuration mismatch visible in source/config |
| **T1 raw score** | **10.0** | |

### T2 - Relationships & Bean Validation (20%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Required relationship coverage | 1.5 | All required one-to-one, one-to-many, many-to-one, and many-to-many relationships are present |
| Owning side and join mapping | 1.5 | Correct `mappedBy`, `@JoinColumn`, `@JoinTable`; schema shape has expected foreign keys/join table |
| Bidirectional helper methods | 1.0 | Methods keep both sides synchronized, e.g. `member.addLoan`, `loan.addItem`, `book.addAuthor` |
| Cascade decisions | 1.5 | Cascade used only for owned child lifecycles; no dangerous broad cascade on shared entities |
| Orphan removal decisions | 1.0 | Used appropriately for `Loan`/`LoanItem` or equivalent owned children; not used on shared references |
| Bean Validation annotations | 1.5 | Uses `@NotNull`, `@NotBlank`, `@Size`, `@Email`, `@Positive`, `@PositiveOrZero` where appropriate |
| Validation execution and messages | 1.0 | Invalid input is validated before persistence and produces readable messages without crashing |
| Relationship safety in output | 0.5 | `toString`, logging, or DTO output avoids infinite recursion and excessive lazy loading |
| Relationship evidence | 0.5 | README/demo evidence proves helper methods/cascade/orphan behavior |
| **T2 raw score** | **10.0** | |

### T3 - Catalog, Member, Lending, and Return Flows (20%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Catalog flows | 1.5 | Create/list/search categories, authors, and books through CLI/service/repository |
| Member flows | 1.0 | Register/list/search members with profile data and validation |
| Lending use case | 2.0 | Creates loan with one or more items, validates member/book/quantity, decrements available copies |
| Transaction and rollback | 2.0 | Loan creation, item creation, and copy decrement occur in one transaction; failure rolls back all changes |
| Return use case | 1.0 | Return updates loan status, `returnedAt`, and available copies correctly |
| Availability protection | 1.0 | Available copies never become negative in normal sequential use |
| Custom exceptions and error handling | 1.0 | Required exceptions or clear equivalents exist; CLI catches and reports domain errors cleanly |
| Layering | 0.5 | Business logic is in services; repositories own persistence; CLI does not run persistence logic directly |
| **T3 raw score** | **10.0** | |

### T4 - JPQL, Named Queries, and Criteria API (20%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Basic JPQL queries | 1.5 | Find by ISBN, keyword search, category/author lists use entity fields and named parameters |
| Joins and relationship queries | 1.5 | Active loans by member email, overdue loans, and loan detail queries use correct joins |
| Ordering and pagination | 1.0 | Book lists/searches have deterministic ordering and `setFirstResult`/`setMaxResults` pagination |
| Named queries | 1.0 | At least two useful `@NamedQuery` definitions are present and called correctly |
| Criteria API dynamic search | 2.0 | Optional filters for keyword/category/author/availability are composed correctly and safely |
| DTO/report projections | 1.5 | Top borrowed books and/or loan status counts use DTO or scalar projection appropriately |
| Query safety and placement | 1.0 | Parameters are bound; no string-concatenated user input; query methods live in repository/query layer |
| Query evidence | 0.5 | README/demo shows expected query outputs |
| **T4 raw score** | **10.0** | |

### T5 - Performance Optimization Evidence (15%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Lazy/eager rationale | 1.5 | Relationship fetch choices are intentional and explained; no blanket eager loading |
| N+1 detection | 1.5 | README/log evidence identifies a concrete BookNest N+1 scenario |
| N+1 fix | 2.0 | Uses fetch join, batch fetching, or DTO projection to reduce query count for that use case |
| Efficient detail/list queries | 1.0 | Uses fetch join for details and pagination/DTOs for lists/reports where appropriate |
| First-level cache demo | 1.5 | Demonstrates two same-id finds in one persistence context return the same managed instance or avoid duplicate SQL |
| Second-level cache handling | 1.0 | Either configures cache for stable lookup data correctly or gives a technically sound reason not to enable it |
| Indexes/constraints for query fields | 1.0 | ISBN/email uniqueness and common filter fields are indexed or constrained where appropriate |
| Performance explanation quality | 0.5 | README/code comments clearly explain generated SQL and why the optimization works |
| **T5 raw score** | **10.0** | |

### T6 - README and Deliverable Quality (10%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Build and run documentation | 2.0 | README gives setup/run commands that are consistent with the project structure |
| README completeness | 3.0 | Setup/run, DB config, schema explanation, id strategy, performance note, feature checklist for T1-T6 |
| Sample data/seed | 1.5 | Provides sample data or seed routine so graders can quickly review the app |
| Code quality and explainability | 2.0 | Clean names, no dead/debug code, no raw types, learner can explain the implementation |
| Deliverable completeness | 1.5 | Required deliverables are present and organized with no generated build output, local DB secrets, or unrelated large files |
| **T6 raw score** | **10.0** | |

---

## 4. Caps and Deductions

Every entry below bounds the **raw 0-10 score of the task it sits under**. The lowest applicable cap for a task wins, caps are never additive, deductions apply after the cap, and the task score is floored at 0. The final score is the weighted sum of the task scores and is never adjusted.

### Every task

Failures that leave no task evidenced at all.

| Trigger | Effect |
|---|---:|
| No meaningful Java source submitted | cap 2.0 |
| Not a Maven project and no runnable/build evidence in files | cap 7.0 |
| Does not use JPA/Hibernate for persistence | cap 4.5 |
| Uses Spring/Spring Boot/Spring Data JPA to hide core Hibernate work | cap 7.0 |
| Deliverables cannot be understood/reviewed from provided files | cap 4.0 |
| Plagiarism copied from another learner | 0 for both parties |
| Code the learner cannot explain in discussion/review | down to 0 on the task it affects |
| Raw types or unchecked casts in meaningful code | -0.5 |
| Leftover debug spam, `printStackTrace` in normal flow, commented-out dead code | -0.3 |

### T1 - Hibernate Project Setup & Entity Mapping

| Trigger | Effect |
|---|---:|
| Data is only in memory; no real database persistence | cap 5.0 |
| Mixed `javax.persistence` and `jakarta.persistence` imports causing fragility | -0.5 |
| Resources not closed / `EntityManagerFactory` lifecycle ignored | -0.5 |

### T2 - Relationships & Bean Validation

| Trigger | Effect |
|---|---:|
| Entities exist but required relationships are mostly absent or incorrect | cap 6.5 |
| Dangerous cascade remove on many-to-many shared entities | -0.7 |

### T3 - Catalog, Member, Lending, and Return Flows

| Trigger | Effect |
|---|---:|
| No end-to-end lending transaction | cap 6.5 |
| Lending can clearly make available copies negative in ordinary sequential use | cap 7.0 |

### T4 - JPQL, Named Queries, and Criteria API

| Trigger | Effect |
|---|---:|
| No JPQL/Criteria query evidence | cap 7.0 |
| User input concatenated into JPQL/SQL query strings | -1.0 |

### T5 - Performance Optimization Evidence

| Trigger | Effect |
|---|---:|
| Blanket `FetchType.EAGER` used to avoid lazy loading errors | -0.7 |

### T6 - README and Deliverable Quality

| Trigger | Effect |
|---|---:|
| Incomplete README | -0.5 |
| Missing required deliverables or project structure is difficult to review | -0.5 |
| Provided files include generated build output, local database files with secrets, IDE-only generated noise, or unrelated large files | -0.3 |

---

## 5. Common point-loss reasons

- **T1:** missing `persistence.xml`, wrong persistence-unit name, in-memory-only database, missing protected no-arg constructors, inconsistent access strategy, enum stored as ordinal.
- **T2:** incorrect owning side, missing `mappedBy`, unsafe `CascadeType.ALL`, cascade remove on many-to-many, helper methods update only one side, validation annotations present but never executed.
- **T3:** lending flow saves partial data on failure, no rollback path, available copies can become negative, return flow does not restore copies, CLI performs persistence logic directly.
- **T4:** JPQL uses table/column names instead of entity/field names, user input is concatenated into queries, no pagination, Criteria query does not actually apply optional filters, report loads full entity graphs unnecessarily.
- **T5:** all relationships are eager, N+1 is described only vaguely, optimization is claimed without query evidence, first-level cache demo uses different persistence contexts.
- **T6:** README omits setup/database instructions, no sample data, generated output or local secrets are mixed into deliverables.

---

## 6. Score sheet

| Task | Score (0-10) | Weight | Weighted |
|---|---:|---:|---:|
| T1 Hibernate Project Setup & Entity Mapping | | 15% | |
| T2 Relationships & Bean Validation | | 20% | |
| T3 Catalog, Member, Lending, and Return Flows | | 20% | |
| T4 JPQL, Named Queries, and Criteria API | | 20% | |
| T5 Performance Optimization Evidence | | 15% | |
| T6 README and Deliverable Quality | | 10% | |
| **Total** | | **100%** | |

Each task score already carries its own caps and deductions, so the weighted sum is the final score — there is nothing left to subtract.

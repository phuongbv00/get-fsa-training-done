# Practice Exam Rubric (INSTRUCTOR ONLY) - StockRoom Inventory API

> **Code:** SBF_PE_02
>
> **Learner brief:** [sbf_practice_exam_02.md](sbf_practice_exam_02.md)
>
> WARNING: **DO NOT distribute this file to learners.** This file holds the
> exact per-criterion grading detail, caps, deductions, and answer expectations
> for graders.

---

## 1. Grading Principle

- Grade observable evidence in submitted source and configuration.
- **No written documentation is required or graded.** This exam assesses code
  only. Judge every criterion from the code and configuration alone, and never
  deduct for an unexplained but correct implementation. A submitted README is
  neither rewarded nor penalised, and a claim in one counts for nothing unless
  the artifacts show it.
- Review the submitted files as evidence; do not require executing the project
  to assign a score.
- This is a **retake exam deliberately scoped at half the workload of
  `SBF_PE_01`** — one entity, four endpoints plus login, one business invariant,
  route-level security only. Do not import expectations from `SBF_PE_01`: a
  second entity, a relationship, a status workflow, ownership rules, or an
  authorization matrix beyond the four rows in the brief are **out of scope** and
  neither earn credit nor cost marks when absent.
- The brief states outcomes rather than implementation steps. Where a criterion
  below names a concrete Spring mechanism, accept any equally correct
  alternative that achieves the same guarantee, and say so in the comment.
  Examples of alternatives that must **not** be penalised:
  - atomicity achieved by a `@Transactional` service method, or by a guarded
    atomic UPDATE (`... SET quantity = quantity + :delta WHERE id = :id AND
    quantity + :delta >= 0`) whose affected-row count drives the rejection, or
    by a pessimistic/optimistic lock;
  - deterministic ordering via `Sort` on `id`, on `createdAt` plus `id`, or a
    configured default sort such as `@PageableDefault(sort = ...)` — any
    explicitly chosen, stable tiebreaker;
  - the `status` filter via a derived query, JPQL, `Specification`, or `Example`;
  - centralized errors via `@RestControllerAdvice`, `@ControllerAdvice`, or a
    `ProblemDetail`-based equivalent.
- Award correctness and coherent integration before breadth. A small, correct
  required flow scores higher than extra features over a broken core.
- **T5 is optional headroom by design.** The "no working security" cap of 8.5
  matches the natural ceiling of a zero on a 15% task, so a submission with a
  flawless core and no security is a legitimate strong result at 8.5, not a red
  flag. Do not deduct further for the omission, and do not treat a partial
  security layer as worse than none beyond what the T5 sub-criteria already
  score. Learners are not told to triage — expect some to spend time in T5 and
  submit a weaker core; score what is there without inferring intent.
- Do not deduct for omitted automated tests, Docker, Actuator, or deployment —
  those are outside this brief.
- Score every task on a 0-10 raw scale, then apply its fixed percentage weight.
- Apply caps before deductions. Floor the final score at 0.

---

## 2. Fixed Task List

| Task ID | Task | Weighted number | Full-mark evidence |
|---|---|---:|---|
| T1 | Foundation, Entity & Persistence | 15% | Standard Maven/Spring Boot layout, separated layers, constructor injection, `Item` with all required fields, name-stable enum storage, server-controlled initial status, unique `sku`, Spring Data repository |
| T2 | REST API & DTO Contract | 25% | All four endpoints with correct statuses and `Location`, request/response DTOs distinct from the entity, deterministic paginated listing, pushed-down `status` filter, focused adjustment DTO, thin controllers |
| T3 | Transactional Stock Adjustment | 25% | All five endpoint outcomes correct, non-negative-quantity invariant enforced atomically, no write on rejection, `updatedAt` changed on success, distinct domain failures |
| T4 | Validation & Error Handling | 20% | DTO constraints matching the brief, validation triggered at the boundary, one centralized handler, one consistent payload, correct 400/404/409/500 mapping, safe 500 |
| T5 | Security: Login, JWT & Role-Based Access | 15% | Persistent accounts with irreversible passwords, login through Spring Security, signed token with server-owned role, cryptographic verification per request, externalized secret, stateless, four-row access matrix with deny-by-default, safe 401/403 |
| | **Total** | **100%** | |

`final_before_deductions = sum(task_score * weighted_number) / 100`, where each
`task_score` is on a 0-10 raw scale.

Note: T3 (the invariant) and T2 (the contract) together carry 50%. A submission
whose stock rule is absent or unconditional cannot reach the 8+ band even with
polished scaffolding — see Caps.

---

## 3. Per-Task Scoring Guide

### T1 - Foundation, Entity & Persistence (15%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Maven and Spring Boot foundation | 1.5 | `pom.xml` targets Java 17+ and Spring Boot 3.x with Web, Data JPA, Validation, and a database driver; standard source layout present. **The Spring Security starter is scored under T5 only** — its absence costs nothing here when T5 is not attempted |
| Layer/package organization | 1.5 | Web, service, repository, entity, DTO, and exception responsibilities are visibly separated |
| Constructor injection | 1.0 | Required dependencies arrive through constructors; no required dependency relies on field injection |
| `Item` field coverage | 2.0 | All seven fields present with coherent Java types (`quantity` an integer type, `status` an enum, timestamps a date/time type — not `String`) |
| Enum and column mapping | 1.0 | `status` is persisted by name, not ordinal (`EnumType.STRING` or an equivalent converter); id generation and column definitions are coherent |
| Server-controlled initial status | 1.0 | Creation establishes `ACTIVE` in application/domain logic; no request path allows the client to set the initial status |
| `sku` uniqueness | 1.0 | Uniqueness is expressed at the schema level (unique constraint/index) and/or enforced before insert; the `^[A-Z]{3}-\d{4}$` shape is represented somewhere |
| Spring Data repository | 0.5 | A Spring Data interface backs persistence; no hand-written JDBC/`EntityManager` CRUD replacing it |
| Configuration quality | 0.5 | Database configuration is present and exposes no secrets |
| **T1 raw score** | **10.0** | |

### T2 - REST API & DTO Contract (25%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Create endpoint | 1.5 | `POST /api/items` accepts a request DTO and returns `201` with the created response body |
| `Location` header | 0.5 | The create response carries a `Location` header addressing the new item |
| Create input is server-safe | 1.0 | The create DTO has no `id`, `status`, `createdAt`, or `updatedAt`; supplying them cannot influence the stored record |
| Get-by-id endpoint | 1.0 | `GET /api/items/{id}` returns the response DTO and delegates the missing case rather than returning `null`/`200` |
| Paginated collection endpoint | 1.5 | `GET /api/items` accepts `page`/`size` and returns a Spring `Page` or an equivalent explicit paginated response |
| Deterministic ordering | 1.0 | Ordering is explicitly chosen and stable across calls — an explicit `Sort`, a unique tiebreaker, or a configured default sort such as `@PageableDefault(sort = ...)`. A bare, unsorted `Pageable` is database insertion order and scores 0 here |
| Pushed-down `status` filter | 1.0 | The filter is applied by the query (derived method, JPQL, `Specification`, or `Example`) and stays paginated; not `findAll()` then filter in Java |
| Adjustment endpoint shape | 1.0 | `PATCH /api/items/{id}/stock` accepts a focused DTO carrying only the adjustment and delegates the rule |
| DTO separation | 1.0 | Request and response types are distinct from `Item`; the entity is not the request or response contract |
| Thin controllers | 0.5 | Controllers contain no repository calls and no rule decisions |
| **T2 raw score** | **10.0** | |

### T3 - Transactional Stock Adjustment (25%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Unknown item rejected | 0.5 | A missing id produces a `404` path, not an empty/`500` result |
| Zero `delta` rejected | 0.5 | `delta == 0` is refused as a bad request (constraint on the DTO or an explicit check) |
| `DISCONTINUED` item rejected | 1.0 | An adjustment on a discontinued item is refused as a conflict before any write |
| Non-negative invariant | 2.5 | A withdrawal exceeding stock on hand is refused as a conflict; the boundary case (`quantity + delta == 0`) is **accepted**; a restock is unbounded |
| Available quantity reported | 0.5 | The rejection message/payload names the quantity actually available |
| Atomicity | 2.0 | Read-check-write is one unit of work: a `@Transactional` service method, a guarded conditional UPDATE driven by affected rows, or an explicit lock. A read in one transaction followed by a write in another scores at most 0.5 here |
| No write on rejection | 1.0 | Every rejection path throws before `save`/flush; no partially mutated managed entity is left to dirty-checking (e.g. the field is not mutated and then checked) |
| `updatedAt` on success | 0.5 | A successful adjustment changes `updatedAt` via an explicit set, a `@PreUpdate` callback, or Spring Data auditing. If the auditing route is used, the enabling configuration must also be present (`@EnableJpaAuditing` plus `@EntityListeners(AuditingEntityListener.class)`) — a bare `@LastModifiedDate` is inert and scores 0 |
| Distinct domain failures | 1.0 | Missing item and rule violation are separate exception types (or equally unambiguous distinct signals), not one generic exception |
| Responsibility placement | 0.5 | The rule lives in the service layer, not in the controller or the repository |
| **T3 raw score** | **10.0** | |

### T4 - Validation & Error Handling (20%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Request constraint coverage | 2.0 | Create DTO constrains `sku` (present + pattern), `name` (present + 2-100), and `quantity` (present + non-negative) with Jakarta constraints matching the brief |
| Adjustment constraint | 0.5 | A null or zero `delta` is rejected as `400`, by either a DTO constraint or an explicit pre-service check (there is no built-in Jakarta non-zero constraint — do not require a custom annotation) |
| Validation trigger | 1.0 | `@Valid`/`@Validated` activates body validation before the service runs |
| Centralized handler | 1.5 | One `@RestControllerAdvice`/`@ControllerAdvice` (or equivalent) owns error mapping; handling is not duplicated across controllers |
| Error payload consistency | 2.0 | One stable shape with at least timestamp, status, code, message, and path across handled failures; validation failures add a field-error map |
| Status mapping | 2.0 | Validation and enum/parse errors → 400; missing item → 404; stock-rule violation and duplicate `sku` → 409; unexpected → 500 |
| Safe unexpected error | 1.0 | The 500 response exposes no stack trace, SQL, or raw internal exception text |
| **T4 raw score** | **10.0** | |

### T5 - Security: Login, JWT & Role-Based Access (15%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Persistent account model | 1.0 | `UserAccount` persists a unique username/email, stored password, and role; roles are `ADMIN` and `STAFF`; at least one account of each role is obtainable (seed, migration, or documented insert). An enabled/locked flag is optional and neither earns nor costs marks |
| Irreversible password storage | 1.5 | An adaptive one-way `PasswordEncoder` (BCrypt or similar) hashes passwords; no plaintext, reversible, or `{noop}` storage anywhere, including the seed |
| Authentication through Spring Security | 1.5 | Login authenticates via `AuthenticationManager`/provider with a database-backed `UserDetailsService`; no manual raw-password comparison |
| Token issuance | 1.5 | Login returns a signed token with type and expiry, carrying a stable subject, server-assigned role, issued-at, and expiration |
| Token verification per request | 2.0 | A security filter verifies signature, algorithm, structure, and expiry before populating the `SecurityContext`; decoding claims without signature verification scores 0 here |
| Externalized secret and statelessness | 1.0 | The signing secret loads from external/environment configuration and is not committed; session management is stateless |
| Access matrix | 1.0 | Login public; create and stock-adjust `ADMIN`; reads `ADMIN` or `STAFF`; the client cannot choose its own role. For the fallback, either `anyRequest().authenticated()` or `anyRequest().denyAll()` is accepted — what fails is leaving unlisted routes permitted |
| Safe 401 vs 403 | 0.5 | Missing/invalid/expired token → `401`; authenticated but insufficient role → `403`; both return a JSON body rather than the container's default HTML error page. Reusing the Task 4 error shape is ideal but not required; a per-request re-check of an enabled/locked flag is credit-neutral |
| **T5 raw score** | **10.0** | |

---

## 4. Caps and Deductions

### Caps

| Issue | Cap |
|---|---:|
| No meaningful Java source submitted | max 2.0 |
| Source is not a recognizable Spring Boot application | max 4.0 |
| Required persistence is replaced by an in-memory Java collection | max 5.0 |
| No create-to-read end-to-end flow is represented in source | max 5.5 |
| No stock-adjustment endpoint is implemented | max 6.0 |
| The stock adjustment accepts every request with no rule check (quantity can go negative) | max 6.5 |
| The check and the write occur in separate transactions or separate service calls, **and** the rule is otherwise correct | max 8.5 |
| No working security: the API is fully anonymous, or no login/token is implemented | max 8.5 |
| Passwords stored in plaintext/reversible/`{noop}` form, or credentials compared manually | max 6.5 |
| Security accepts an unsigned/unverified/tampered token, or trusts a client-supplied role | max 7.0 |
| Controllers contain most persistence and business logic; no meaningful service boundary | max 7.0 |
| The JPA entity is used directly as both request and response contract throughout | max 7.5 |
| Submission files are too incomplete or disorganized to identify required behavior | max 4.0 |

When several caps apply, use the lowest applicable cap; do not add caps together.

### Deductions

| Issue | Deduction |
|---|---:|
| Field injection used for required application dependencies | -0.3 |
| Enum persisted by ordinal instead of name | -0.3 |
| Collection endpoint loads an unbounded `findAll()` result | -0.5 |
| Pagination ordering is unstable or absent | -0.3 |
| `status` filter applied in Java after loading all rows | -0.3 |
| Boundary case `quantity + delta == 0` incorrectly rejected (off-by-one) | -0.3 |
| A rejected adjustment still changes `updatedAt` or the stored quantity | -0.5 |
| A rule violation is returned as `200 OK` | -0.5 |
| Raw exception message or stack trace exposed to clients | -0.7 |
| Raw password, hash, bearer token, or signing secret written to logs or a response | -0.7 |
| Hard-coded signing secret or real seeded password committed | -0.7 |
| Generated output, IDE-only noise, or unrelated large files included | -0.2 |
| Meaningful dead/debug code left in the submission | -0.2 |

Apply a deduction once per issue category unless the issue causes distinct,
independent harm. Do not deduct twice for a defect already reflected in a task
score.

---

## 5. Common point-loss reasons

- **T1:** missing Validation dependency, mixed
  `javax`/`jakarta` imports, field injection, `quantity` or timestamps typed as
  `String`, ordinal enum mapping, client-settable initial status, no unique
  constraint on `sku`.
- **T2:** entity returned directly as the response, no `Location` header,
  unpaginated list, ordering left to the database, `status` filtered in Java
  after `findAll()`, the adjustment DTO carrying the whole item, repository
  calls inside the controller.
- **T3:** the negative-quantity check missing or off by one, `DISCONTINUED`
  items adjustable, the check running in a different transaction from the write,
  the entity mutated before the check so dirty-checking persists a rejected
  change, one generic `RuntimeException` for every failure, the rule implemented
  in the controller.
- **T4:** constraints placed on the entity instead of the request DTO, missing
  `@Valid`, error bodies that differ per handler, duplicate `sku` mapped to 500
  instead of 409, unknown enum values mapped to 500, stack traces reaching the
  client.
- **T5:** in-memory users as the final account store, `{noop}`/plaintext
  passwords, manual credential comparison, role read from the request instead of
  the account, JWT parsed but not signature-verified, hard-coded secret,
  session-based (non-stateless) security, matcher order leaving `POST
  /api/items` open, everything failing as 403.

Out-of-scope work that must **not** be rewarded or penalised: a second entity or
relationship, a status workflow beyond `ACTIVE`/`DISCONTINUED`, ownership rules,
automated tests, Docker, Actuator, deployment.

---

## 6. Score sheet

| Task | Score (0-10) | Weight | Weighted |
|---|---:|---:|---:|
| T1 Foundation, Entity & Persistence | | 15% | |
| T2 REST API & DTO Contract | | 25% | |
| T3 Transactional Stock Adjustment | | 25% | |
| T4 Validation & Error Handling | | 20% | |
| T5 Security: Login, JWT & Role-Based Access | | 15% | |
| **Total** | | **100%** | |

Caps applied: _______________________________________________

Deductions: __________________________________________ = - ____

Final score: ______ / 10

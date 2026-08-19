<!-- Shipped as a worked example. Copied from a real assessment and kept intact so the shape, tone, and depth are the genuine article rather than a sketch. -->

> **This is the brief to imitate.** Three sections, bullet-led tasks, per-task constraints, a checklist of deliverables, and exactly on its four-page budget for a two-hour exam.

# Practice Exam - StockRoom Inventory API

> **Code:** SBF_PE_02
> **Duration:** 2 hours
> **Topics:** Spring Boot | dependency injection | REST API | DTOs | Spring Data JPA | transactions | validation | exception handling | Spring Security | JWT

---

## 1. Problem Statement

StockRoom runs a warehouse. Staff receive deliveries and pick goods all day,
and the manager needs a system of record for what is actually on the shelf.

Build that system of record as a REST API over a relational database. Three
rules define it:

- **Stock never goes negative.** Two people picking the last unit at the same
  moment must not both succeed.
- **Discontinued lines are frozen.** Nobody may move their stock.
- **The manager registers items and corrects stock. Floor staff may look, not
  touch.**

---

## 2. Tasks

### Task 1 - Foundation, Entity & Persistence (15%)

- Maven Spring Boot project, standard layout, Java 17+ and Spring Boot 3.x.
- Web, service, repository, entity, DTO and exception responsibilities visibly
  separated. Equivalent package names are fine.
- Constructor injection throughout.
- Persist through a Spring Data repository into H2, PostgreSQL or MySQL —
  **not** a hand-written `EntityManager`/JDBC layer, and **not** an in-memory
  Java collection. Lombok, MapStruct and Flyway are permitted.
- One entity, `Item`:

| Field       | Requirement                                                     |
| ----------- | --------------------------------------------------------------- |
| `id`        | Generated primary key                                           |
| `sku`       | Required, unique, matching `^[A-Z]{3}-\d{4}$` (e.g. `ABC-1024`) |
| `name`      | Required, 2-100 characters                                      |
| `quantity`  | Required, integer, never negative — stock on hand               |
| `status`    | Enum: `ACTIVE`, `DISCONTINUED`                                  |
| `createdAt` | Set when the item is created                                    |
| `updatedAt` | Changes whenever the item changes                               |

- Enum values must survive a reordering of the enum constants.
- A new item always starts `ACTIVE`; the client cannot choose the initial status.
- `DISCONTINUED` items are established outside the API, via seed data or
  directly in the database. **No status-change endpoint is required.**

### Task 2 - REST API & DTO Contract (25%)

| Method  | Path                    | Required behavior                        |
| ------- | ----------------------- | ---------------------------------------- |
| `POST`  | `/api/items`            | Create an item, return `201 Created`     |
| `GET`   | `/api/items/{id}`       | Return one item, or `404 Not Found`      |
| `GET`   | `/api/items`            | Paginated list; optional `status` filter |
| `PATCH` | `/api/items/{id}/stock` | Apply a stock adjustment (Task 3)        |

- Request and response DTOs must be distinct from the entity. Exposing the JPA
  entity as either contract is **not allowed**.
- `POST /api/items` accepts `sku`, `name` and the initial `quantity` only, and
  returns the created resource plus a `Location` header addressing it.
- The list endpoint accepts `page` and `size`; ordering must be deterministic
  across repeated calls over identical data.
- The `status` filter must not load every row before filtering.
- The adjustment request body carries only the adjustment itself.
- Controllers hold no business decisions and no database access.

### Task 3 - Transactional Stock Adjustment (25%)

`PATCH /api/items/{id}/stock` applies a signed integer `delta` — positive is a
restock, negative is a withdrawal. This is the core of the exam.

> **An item's `quantity` must never become negative, and a `DISCONTINUED` item
> must never be adjusted.**

- Unknown item id → `404`.
- `delta` of `0` → `400`.
- Item is `DISCONTINUED` → `409`.
- Withdrawal larger than stock on hand → `409`, reporting the quantity actually
  available. Withdrawing the last unit exactly must succeed.
- Otherwise: apply the adjustment, change `updatedAt`, return the updated item.
- **Atomicity.** Reading the quantity, checking the rule and writing the new
  value are one atomic unit of work. There must be no point at which the stored
  quantity is negative, or at which the check passed against a value that is no
  longer current.
- **No side effects on rejection.** A rejected adjustment leaves the item — and
  `updatedAt` — exactly as it was.
- A missing item and a rule violation are different domain failures, not one
  generic exception.

### Task 4 - Validation & Error Handling (20%)

- Validate request DTOs at the HTTP boundary with Jakarta Bean Validation.
- Map every handled failure through **one** centralized place to one consistent
  JSON shape — timestamp, status, code, message, path, plus a field-error map
  for validation failures:

```json
{
  "timestamp": "2026-08-04T09:30:00Z",
  "status": 400,
  "code": "VALIDATION_FAILED",
  "message": "Request validation failed",
  "path": "/api/items",
  "fieldErrors": { "sku": "must match \"^[A-Z]{3}-\\d{4}$\"" }
}
```

- Your messages and code names may differ; the shape must not.
- Invalid fields, unknown enum values → `400`. Missing item → `404`.
  Stock-rule violation, duplicate `sku` → `409`. Anything unexpected → `500`.
- No stack trace, SQL or internal exception detail may reach the client.

### Task 5 - Security: Login, JWT & Role-Based Access (15%)

Ownership rules are **not** part of this exam — role-level access is enough.

- Persist a `UserAccount`: unique username or email, stored password, and a role
  (`ADMIN` or `STAFF`).
- The original password must not be recoverable from the database, logged, or
  returned. Plain-text, reversible and `{noop}` storage are **not allowed**.
- At least one account of each role must exist; a startup seed is fine. No real
  password may be committed.
- `POST /api/auth/login` accepts credentials and returns an access token signed
  with a maintained JWT library (JJWT or Nimbus), with its type and expiry.
  Credentials must be checked through Spring Security's authentication
  machinery, not by comparing password strings.
- The token carries a stable subject, the role the **server** assigned, an
  issued-at time and an expiration. A client must never choose its own role.
- Every authenticated request has its token cryptographically verified —
  signature, algorithm, structure, expiry — before any identity is trusted.
  Reading claims without verifying the signature is not authentication.
- The signing secret loads from external configuration. Sessions are stateless.

| Route                                            | Minimum access   |
| ------------------------------------------------ | ---------------- |
| `POST /api/auth/login`                           | Public           |
| `POST /api/items`, `PATCH /api/items/{id}/stock` | `ADMIN`          |
| `GET /api/items`, `GET /api/items/{id}`          | `ADMIN`, `STAFF` |
| Anything else                                    | Denied           |

- Missing, invalid or expired token → `401`. Valid account, insufficient role →
  `403`. Both return a JSON body, not the container's default HTML error page.

---

## 3. Deliverables

- [ ] A single zip named `<StudentID>_sbf_p_exam_02.zip`, where `<StudentID>` is
      exactly your id on the class roster (for example `PhuongBV3`).
- [ ] Inside it, the Maven project folder containing `pom.xml`,
      `src/main/java/` and `src/main/resources/`.
- [ ] Environment placeholders, where present, for the JWT secret and seeded
      credentials — never the real values.
- [ ] **Excluded:** `target/`, `.idea/`, `.vscode/`, real passwords, tokens,
      signing keys, and unrelated build output.

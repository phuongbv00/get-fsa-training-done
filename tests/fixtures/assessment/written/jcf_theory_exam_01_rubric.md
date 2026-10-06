# Theory Exam - Java and Persistence Interview Questions Rubric (INSTRUCTOR ONLY)

> **Code:** FR_JCF_TE_01
> **Learner brief:** [jcf_theory_exam_01.md](jcf_theory_exam_01.md)
> WARNING: **DO NOT distribute this file to learners.**

## 1. Grading Principle

Grade submitted files as evidence; do not execute learner code. Each question is scored on its own row; award partial credit for correct, relevant points even if another question is blank. Each raw task score is 0-10 and is the sum of its question rows. Apply that task's caps before weighting; the lowest applicable cap wins. Final score = sum(raw score * weight) / 100. Do not adjust the total afterwards.

The questions are deliberately short, as in an interview; the evidence column lists what a strong answer covers. Full marks for a row need its core points, explained as mechanism (how and why) rather than a bare definition. A bare definition with no mechanism or example earns at most half of the row. Equivalent technically correct answers receive equal credit; wording does not need to match. Correct depth beyond the listed points earns no extra marks but can compensate for one minor missing point in the same row. Blank or unrelated answers earn zero for that question.

## 2. Fixed Task List

| Task ID | Task | Weighted number | Full-mark evidence |
|---|---|---:|---|
| T1 | Java Platform and Toolchain | 25% | Q1-Q5; criteria in T1 below |
| T2 | OOP, Exceptions and Testing | 25% | Q6-Q10; criteria in T2 below |
| T3 | Collections and Streams | 25% | Q11-Q15; criteria in T3 below |
| T4 | JDBC and JPA Persistence | 25% | Q16-Q20; criteria in T4 below |
| | **Total** | **100%** | |

## 3. Per-Task Scoring Guide

### T1 - Java Platform and Toolchain (25%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Q1 JVM/JRE/JDK and source to execution | 3.0 | JVM executes bytecode; JRE = JVM + standard class libraries; JDK = JRE + development tools (`javac`, `jar`, debugger); JDK to develop, a runtime to run (also accept: modern JDKs no longer ship a separate JRE). `javac` compiles `.java` to platform-independent bytecode (`.class`, optionally in a JAR); the JVM loads the classes (class loader), interprets the bytecode and JIT-compiles hot code to native machine code; mentioning bytecode verification is a plus, not required. Portability: same bytecode, platform-specific JVM. |
| Q2 Stack and heap | 2.0 | Stack: one frame per method call holding local variables and references, freed when the method returns, per thread. Heap: objects, shared, managed by GC. `qty` (value 3), `p` and `q` (references) in `run()`'s frame; one `Product` object on the heap, referenced by both `p` and `q`. Strong answers mention StackOverflowError (deep recursion) vs OutOfMemoryError (heap full), or that the object becomes unreachable after `run()` returns. |
| Q3 Garbage collection | 1.5 | GC frees heap objects that are no longer reachable from GC roots (stack references, static fields, active threads); no manual `free`. Generational idea: most objects die young, so the young generation is collected often and survivors are promoted to the old generation. `System.gc()` is only a hint; leaks are still possible when unneeded objects stay referenced (static collections, caches). Any two of the last three points for full marks. |
| Q4 String pool and equality | 1.5 | Literals are interned in a pool and shared, which is safe because `String` is immutable. `==` compares references, `equals` compares content. `a == b` true (same pooled object); `a == c` false (`new` creates a separate heap object); `a.equals(c)` true. |
| Q5 POM and Maven commands | 2.0 | POM: coordinates groupId/artifactId/version, packaging, properties (e.g. `maven.compiler.release`), dependencies with scope (e.g. `test`), build plugins. Commands with their effect: `clean`, `compile`, `test`, `package`, `install` (at least four), noting that a phase runs all earlier lifecycle phases. |
| **T1 raw score** | **10.0** | |

### T2 - OOP, Exceptions and Testing (25%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Q6 Four principles | 2.0 | Encapsulation (hide state, expose operations that keep it valid), inheritance (a class specialises another), polymorphism (one reference type, behaviour chosen by the object's runtime type), abstraction (expose what, hide how, via interfaces/abstract types). Relates each to class or object, and explains how they work together: abstraction defines the contract, inheritance/implementation provides variants, polymorphism lets clients use any variant through the contract, encapsulation keeps each object valid. |
| Q7 Encapsulation | 1.5 | Private `balance`; no public setter; `deposit`/`withdraw` validate (positive amount, sufficient funds) and reject violations, so the invariant holds for every object. Notes that getters and setters for every field merely hide state without protecting it. |
| Q8 Polymorphism and its goal | 2.5 | Real-world example with a supertype and several implementations (e.g. `PaymentMethod` with card, e-wallet, cash), and client code that depends only on the supertype. Goal: substitutability, so client code works unchanged with any current or future subtype (extensibility, low coupling). Distinguishes overriding (run-time dispatch, the mechanism behind this) from overloading (compile-time, same name, different parameters). |
| Q9 Inheritance vs composition | 2.0 | Inheritance = is-a, reuses the parent's implementation, fixed at compile time and tightly coupled (parent changes can break subclasses). Composition = has-a, holds a collaborator (often behind an interface) and delegates, can be swapped at run time. Prefer composition when the relation is not a true is-a or behaviour must vary; one concrete example. |
| Q10 Exceptions and failure tests | 2.0 | Checked exceptions (subclasses of `Exception` outside `RuntimeException`, e.g. `IOException`, `SQLException`) must be caught or declared with `throws`; used for recoverable external conditions. Unchecked (`RuntimeException`, e.g. `IllegalArgumentException`, `NullPointerException`) need no declaration; used for programming or contract errors. JUnit 5: `assertThrows(IllegalArgumentException.class, () -> service.charge(-1))`, optionally asserting the message. Strong answers note that catching the exception in an empty `catch` makes the test pass even when nothing is thrown. |
| **T2 raw score** | **10.0** | |

### T3 - Collections and Streams (25%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Q11 ArrayList vs LinkedList | 1.5 | ArrayList: backing array grown by copying; `get(i)` O(1), add at end amortised O(1), insert/remove in the middle O(n). LinkedList: doubly linked nodes; `get(i)` O(n), insert O(1) once positioned, more memory per element. ArrayList is the usual default (contiguous memory, cache-friendly). |
| Q12 HashMap and the equals/hashCode contract | 3.0 | `put`: compute the key's hash from `hashCode()`, map it to a bucket index; empty bucket stores a new node; otherwise compare hash and `equals` to replace an existing key's value, or add a node on collision. `get` follows the same path. Resize (capacity doubled, entries rehashed) when size exceeds capacity x load factor (0.75); long buckets become trees (Java 8+); average O(1). Contract: equal objects must have equal hash codes (unequal objects may collide). Broken contract: equal keys land in different buckets, so duplicates appear and lookups fail; mutating a key's equality fields after insertion loses the entry. |
| Q13 Map implementations | 1.5 | HashMap: hash table, no order guarantee, O(1) average. LinkedHashMap: hash table plus linked list, insertion (or access) order. TreeMap: red-black tree, sorted keys, O(log n), keys `Comparable` or a `Comparator`. |
| Q14 Collection choice | 2.5 | a) `HashMap<String, Product>`; b) `ArrayList`; c) `LinkedHashSet`; d) `TreeMap`/`TreeSet` or a sorted structure, handling equal scores; e) `ArrayDeque`/`LinkedList` as `Queue`; f) `HashMap<String, Integer>`. Each choice justified by the underlying structure and cost, not by name only. |
| Q15 Stream API | 1.5 | A stream is a pipeline of operations over a source (e.g. a collection) that does not store data or modify the source. Intermediate operations (`filter`, `map`, `sorted`) return a new stream and are lazy; terminal operations (`collect`, `forEach`, `count`, `reduce`) produce a result or side effect and trigger execution. A stream can be consumed only once. A short pipeline example. |
| **T3 raw score** | **10.0** | |

### T4 - JDBC and JPA Persistence (25%)

| Sub-criterion | Raw points | Full-mark evidence |
|---|---:|---|
| Q16 PreparedStatement and resources | 2.0 | `Statement` runs SQL text as given, so concatenated input can change the query (SQL injection, e.g. `' OR '1'='1`). `PreparedStatement` uses `?` placeholders and sends values separately, so input stays data; it can also be precompiled and reused. Connections, statements and result sets hold database and driver resources; leaks exhaust the pool or cursors, so close them with try-with-resources, which works even on exceptions. |
| Q17 Transactions and ACID | 2.5 | Transaction = a unit of work that succeeds or fails as a whole. Atomicity, Consistency, Isolation, Durability, each explained in one line. JDBC: same `Connection`, `setAutoCommit(false)`, run both writes, `commit()` after both, `rollback()` on failure; with auto-commit on, each statement commits alone. |
| Q18 ORM, JPA, Hibernate | 1.5 | ORM maps classes/objects to tables/rows and relationships to foreign keys. JPA is the specification (API); Hibernate is an implementation (provider). JDBC for full SQL control and simple or bulk queries; JPA for domain models with relationships and less mapping code. |
| Q19 Persistence context and lifecycle | 2.0 | Persistence context = the set of managed entities of an `EntityManager`, one instance per id (first-level cache), with dirty checking flushing changes at commit. Lifecycle: new/transient, managed (`persist`, `find`), detached (context closed, `detach`, `clear`), removed (`remove`); `merge` reattaches a copy. |
| Q20 Fetching and N+1 | 2.0 | LAZY loads the association on first access; EAGER loads it with the owner. Accessing a lazy association after the `EntityManager` closes raises `LazyInitializationException`. N+1: one query for a list plus one per element for its association. Detect by counting SELECTs in the SQL log; fix with `JOIN FETCH` (LEFT to keep parents without children), entity graph or batch fetching, not blanket EAGER. |
| **T4 raw score** | **10.0** | |

## 4. Caps and Deductions

Caps apply only to the named task. Do not penalize the same omission again outside its criteria.

### T2 - OOP, Exceptions and Testing

| Trigger | Effect |
|---|---:|
| Q8 explains polymorphism only as the existence of overloading/overriding, with no substitution through a supertype | cap 7.0 |

### T3 - Collections and Streams

| Trigger | Effect |
|---|---:|
| Q12 states that equal objects may have different hash codes | cap 6.0 |

### T4 - JDBC and JPA Persistence

| Trigger | Effect |
|---|---:|
| Q17 transaction has no rollback on failure | cap 6.0 |
| Q16 recommends building SQL by concatenating input values | cap 6.0 |

## 5. Common point-loss reasons

- **T1:** saying Java compiles straight to machine code; placing objects on the stack; `a == c` true; listing Maven commands without what they do.
- **T2:** listing the four principles without how they relate; polymorphism shown as overloading only; getters and setters for every field presented as encapsulation; exceptions tested with an empty `catch` instead of `assertThrows`.
- **T3:** describing HashMap without the role of `equals` inside a bucket; choosing a collection by habit with no structural reason; claiming intermediate stream operations run immediately.
- **T4:** committing after the first statement; closing only the connection; recommending EAGER everywhere as the N+1 fix.

## 6. Score sheet

| Task | Score (0-10) | Weight | Weighted |
|---|---:|---:|---:|
| T1 Java Platform and Toolchain | | 25% | |
| T2 OOP, Exceptions and Testing | | 25% | |
| T3 Collections and Streams | | 25% | |
| T4 JDBC and JPA Persistence | | 25% | |
| **Total** | | **100%** | |

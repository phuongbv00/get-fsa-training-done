# Theory Exam - Java and Persistence Interview Questions

> **Code:** FR_JCF_TE_01
> **Level:** FR
> **Duration:** 60 minutes
> **Topics:** JCF-K1 | JCF-K2 | JCF-K3 | JCF-K4

---

## 1. Problem Statement

Answer the 20 interview questions below as you would explain them to an interviewer. Answers are scored on correctness and depth: explain how and why, not only what, and add a short example or code fragment where it helps.

## 2. Tasks

### Task 1 - Java Platform and Toolchain (25%)

**Q1.** What is the difference between the JVM, the JRE and the JDK? Describe the process from a `.java` file to a program running on a machine.

**Q2.** What is the difference between the stack and the heap? In the code below, where do `qty`, `p`, `q` and the `Product` object live?

```java
static void run() {
    int qty = 3;
    Product p = new Product("P1");
    Product q = p;
}
```

**Q3.** How does garbage collection work in Java?

**Q4.** What is the String pool? Give the result of each comparison below and explain it.

```java
String a = "java";
String b = "java";
String c = new String("java");
// a == b ?   a == c ?   a.equals(c) ?
```

**Q5.** Describe the structure of a `pom.xml` and the Maven commands you use most often.

### Task 2 - OOP, Exceptions and Testing (25%)

**Q6.** Explain the four OOP principles and how they relate to classes and objects.

**Q7.** What is encapsulation? Illustrate it with a `BankAccount` class whose balance can never become negative.

**Q8.** Give a real-world example of polymorphism. What is the goal of polymorphism?

**Q9.** What is the difference between inheritance and composition? When should you prefer composition?

**Q10.** What is the difference between checked and unchecked exceptions? How do you test in JUnit 5 that a method throws an exception?

### Task 3 - Collections and Streams (25%)

**Q11.** What is the difference between `ArrayList` and `LinkedList`? When do you use each?

**Q12.** How does a `HashMap` work when you `put` and `get` an entry? What happens if `equals()` and `hashCode()` break their contract?

**Q13.** What is the difference between `HashMap`, `LinkedHashMap` and `TreeMap`?

**Q14.** Choose a suitable collection for each need below and explain why:

- a) look up a product by its unique code many times;
- b) keep order lines in arrival order, duplicates allowed, often read by position;
- c) remove duplicate e-mail addresses but keep the first-seen order;
- d) keep a leaderboard always sorted by score;
- e) process jobs first-in, first-out;
- f) count how many times each word appears in a text.

**Q15.** What is the Stream API? What is the difference between intermediate and terminal operations?

### Task 4 - JDBC and JPA Persistence (25%)

**Q16.** What is the difference between `Statement` and `PreparedStatement`? Why must JDBC resources be closed?

**Q17.** What are a transaction and ACID? In JDBC, how do you make two writes one transaction?

**Q18.** What is an ORM? What is the difference between JPA and Hibernate? When do you choose JDBC and when JPA?

**Q19.** What is the persistence context? Describe the lifecycle of an entity.

**Q20.** What is the difference between `LAZY` and `EAGER` fetching? What is the N+1 query problem and how do you fix it?

## 3. Deliverables

- Submit only the supplied template `jcf_theory_exam_01_answer_template.md`, completed and renamed `jcf_t_exam_01_<fpt_account>.md` with your FPT account as on the class roster (e.g. `jcf_t_exam_01_PhuongBV3.md`). No zip or PDF; do not copy the questions into it.

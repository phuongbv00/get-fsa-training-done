# Writing style

Every feature writes for one of two readers: a **trainee**, who reads a brief, a
lecture note or a lab under time pressure, or an **instructor**, who reads a
rubric or a report and has to act on it. These rules hold for both, in every
language.

## Plain words

- **Plain English.** Short sentences and common words. The trainee is often
  reading a second language; a sentence that needs reading twice costs exam
  time. "Explain what problems the `skills` column causes" beats "Where does
  the `skills` column go wrong, and with what do you replace it?"
- **Ask the question, not its answer key.** An interview-style question names
  the subject and stops: "Describe the process from a `.java` file to a program
  running on a machine." Listing the points a strong answer covers ("class
  loading, verification, JIT...") turns a question into a checklist and
  belongs in the rubric.
- **Digits for numbers.** "Complete the 5 tasks below", "at least 3 user
  stories", "exactly 1 `CREATE INDEX`". A count written as a word is easy to
  miss in a requirement.
- **State a rule once, where it applies.** A constraint lives in the task it
  constrains; a business rule lives with the entity or feature it governs, not
  in a general note at the end.

## Professional tone

- Address the trainee directly and neutrally: "Submit...", "Your query must...".
  No reassurance, no jokes, no asides such as "the file is yours, edit it
  freely".
- No advice or strategy in anything a trainee is graded on: no "start with the
  simplest case", no "if time runs short". Weights already say where the marks
  are.
- Comments a trainee receives are about the work, never about the grading
  process.

## Examples and placeholders

- The example account is always `PhuongBV3` — in archive names, template
  placeholders and sample rows. Never a real trainee's account.
- Sample people in generated material (backlogs, personas, team members) use
  invented English short names, such as `AlexDF` for "Alex De Fleu".
- Domains are invented products with a short name — ClinicDesk, LibraryDesk,
  StockDesk — never a real company.

## Vietnamese

Read `references/common/language_vn.md` before writing anything in Vietnamese.

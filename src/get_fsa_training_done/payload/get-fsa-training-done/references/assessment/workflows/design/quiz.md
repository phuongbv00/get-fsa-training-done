# Workflow — quiz

A fast, live question set. Short timers, run in class.

**Produces:** `<stem>.csv` (instructor-only master), `<stem>_blooket.csv`

## 1. Confirm the structure — always ask

Even when the user gave a topic, confirm the shape before drafting anything.
Propose defaults, adjusted by the level from `references/assessment/levels.md`:

| Setting | Default |
|---|---|
| Question count | 40 |
| Duration | 30 minutes |
| Options per question | 4 |
| Time limit | Easy 5s, Medium 10s, Hard 20s |
| Bloom mix | from the level |
| Difficulty mix | from the level |
| Unit mix | one bucket per topic in scope |

Ask `FSA` for the counts rather than doing the arithmetic:

```bash
FSA assessment levels show --level <LEVEL> [--band <BAND>] --count 40
```

Report the plan — count, duration, all three distributions, option count, time
map, scope boundaries, delivery format — and **do not draft a single question
until it is confirmed.**

## 2. Read the question standard

Read `references/assessment/question_guidelines.md` in full before drafting. It is short
and it is the difference between a bank that discriminates and one that does
not.

## 3. Write the master CSV — `<stem>.csv`

Twelve columns, exactly:

```
No,Unit/Lecture,Bloom Level,Difficulty,Question,Answer 1,Answer 2,Answer 3,Answer 4,Correct Answer(s),Time Limit (sec),Note
```

- `Correct Answer(s)` is the 1-based option number — `2`, or `1,3` for multi.
- Fill all four answers for every question.
- `Time Limit (sec)` follows the confirmed map.
- `Note` is your design rationale, one line. Instructor-only.

### Two formatting rules that break imports

**No backticks.** Neither platform renders Markdown; a backtick either breaks the
import or appears literally on screen. Write code fragments as bare text. If a
question is genuinely *about* the character, name it in words.

**No raw tags or generics.** Both platforms parse imported text as markup, so
anything tag-shaped is swallowed mid-sentence and never reaches the learner —
`<CartPanel />`, `</>`, `<div>`, `List<String>`, `ResponseEntity<BookResponse>`.
Two ways out, in order of preference:

1. **Name it in prose** — "a CartPanel element", "a JSX fragment", "a
   JpaRepository of Book with a Long id". This reads better in a quiz anyway. If
   a tag appears several times in one question, restructure so the options carry
   only the part being tested.
2. **Space every bracket**, when the literal syntax is what is being assessed:
   `List < String >`, `< CartPanel / >`.

Operators keep their normal form — `user -> user.isActive()`, `score >= 5`,
`Country <> 'Germany'` — since they never read as tags.

**This file contains the answers. It is instructor-only, same status as a
rubric.**

## 4. Generate the import file

```bash
FSA assessment emit blooket --master "<output_dir>/<stem>.csv" \
                 -o       "<output_dir>/<stem>_blooket.csv"
```

Never hand-write it. The emitter handles the title row Blooket needs for
delimiter detection and the 300-second cap; getting either wrong produces an
import error that points somewhere else entirely.

## 5. Verify

```bash
FSA assessment verify --type quiz \
  --master  "<output_dir>/<stem>.csv" \
  --blooket "<output_dir>/<stem>_blooket.csv" \
  --level   "<LEVEL>" \
  --expect-count 40
```

`--level` takes the band with it for the banded levels — `UP_SKILL:mid` — and
the level alone for `CPL` and `FR`. It supplies the quiz time map and compares
the Bloom and difficulty mix against the level's defaults; drift is reported as
a warning, never an error. Pass `--time-map Easy=5,Medium=10,Hard=20` only when
the confirmed map differs from the level's.

Then tally the actual distribution — by Bloom level, by unit, by difficulty —
against the confirmed targets and report any material drift.

## 6. Verifier agent

Run `references/assessment/verifiers/quiz.md` with the confirmed plan, the generated
paths, the `FSA assessment verify` output, and the distribution tallies.

# Capstone Project Verifier Agent

Use after generating or editing a capstone brief, spec, and rubric.

`FSA assessment verify --type capstone_project` has already checked that the seven spec
sections exist, that the sprint table numbers run 1..N with sane dates, that
D01–D05 each map to exactly one task and are due in exactly one sprint, that
every `Sprint N` the brief mentions exists, that the checkpoint defines gates
G1–G5 and the rubric's caps name them, that sprint-process and
individual-contribution tasks both exist and are separate, and that the weights
sum to 100%. **Do not re-check those.** Judge whether the thing is actually
gradable and actually buildable.

## Inputs

- Brief, spec, and rubric paths, plus the rendered PDF.
- Confirmed generation plan, including the confirmed **level** and band.
- `references/levels.md`, for that level's expected calibration.
- `FSA assessment verify` output.

## Verification focus

### Scope fits the team and the time

The spec states a team size and a number of sprints. Give a realistic estimate
of the core scope in person-days and say plainly whether it fits. Capstone
briefs fail far more often by being too large than too small, and an
over-scoped project produces rushed work that grades badly for reasons the
rubric never intended to measure.

Check the bonus work is genuinely optional — its weight should be small enough
that a team ignoring it can still score well. A "bonus" carrying 30% is
mandatory work under a friendlier name.

### The sprint calendar is a plan, not a partition

The dates parse and the deliverables land in exactly one sprint each — that much
is already checked. What is left is whether the split is workable: a sprint that
owns D04 Source Code with nothing due before it has no intermediate evidence,
and
a sprint whose window is shorter than the work in its row will produce a
checkpoint every team fails for reasons the rubric never meant to measure.

Say plainly whether each sprint's load fits its window at the stated team size,
the same way you estimate total scope below.

### The checkpoint gates can actually be checked

Read the `## Sprint checkpoint` section as the instructor who will fill the form
at the sprint review. Every gate should be answerable in under a minute from
artifacts that already exist: a tag date, a folder listing, two CSV exports. A
gate that needs the instructor to reconstruct what happened is not a gate.

Check the caps in rubric section 4 are proportionate. A missing review record
that caps individual contribution at 7.0 is a real consequence; one that zeroes
the sprint is a team destroyed by an administrative slip.

### T6 does not re-grade T1–T5

The sprint-process task scores whether the process happened on the dates it
claimed to. The deliverable tasks score the artifacts. If T6's scoring guide
contains adjectives about document quality, it has drifted into T2 or T3 and a
weak team loses the same points twice.

### The individual can be separated from the team

T7 scores the person. Read its full-mark evidence and ask whether two graders
looking at the same team would give the same member the same number. "Contributed
actively" is not gradable; "commits across at least three of the five
deliverable areas, and presented that part at the defence" is.

Then check the team tasks do not quietly double-count individual work, and that
a strong member on a weak team is not capped by their team's artifacts alone.

### Process criteria have dated evidence

Where a criterion is about how the team worked — backlog, sprint reviews, the
WBS — the evidence must be something with a timestamp. A backlog written the
night before the defence satisfies a criterion that asks only for a backlog to
exist, and satisfies nothing that asks for it to have guided the work.

The checkpoint is what makes this possible: it produces the dated artifacts
before anyone could know they would be needed. Flag any process criterion whose
evidence is *not* something the checkpoint already collects — it is asking for
something that will not exist at the defence.

### The stack constraint is enforceable

The spec mandates a stack. Check the rubric can actually tell whether it was
followed by reading the repository, and that the brief does not simultaneously
invite a choice the spec forbids.

### The demo is scored on something

If D05 carries weight, the rubric needs criteria a grader can apply while
watching a defence — not just "presented well". Per-member speaking, a working
live demo rather than a recording, the ability to answer a question about their
own code.

### Deliverable rules are stated where they bite

Diagram-as-code, the public repository, the `docs/` layout: these belong in the
deliverable bullets the team reads, not only in the rubric that grades them.
Flag any rule the rubric penalises that the brief never states.

### Level calibration

Check the scope, ambiguity, and rubric strictness match the level's row in
`references/levels.md`. A capstone at `CPL` should be guided; one at `UP_SKILL
senior` should require architectural decisions the team has to defend.

### Language

Brief, spec, and the generated sprint pack are all in the confirmed language —
English unless the user asked otherwise. The rubric is always English, because
`verify` and the grading pipeline parse its headings.

Flag any language left over from an earlier draft. A brief that is half one
language and half another grades differently for the same work, and a spec whose
`## Sprint checkpoint` section does not match the handout means the generator was
run with a different `--lang` than the rest, or its output was edited by hand.

## Output

```text
VERDICT: pass | needs_revision
STRUCTURE: <brief, spec, and rubric shape notes>
CONTENT: <scope feasibility, with a person-day estimate against team size and duration>
SPRINTS: <whether each sprint's load fits its window, and whether the gates are checkable>
RUBRIC: <gradability, especially the sprint-process and individual-contribution tasks>
REVISIONS_REQUIRED:
- <actionable item, or "none">
```

# Task — Render the brief

Turn a brief into the A4 PDF a trainee reads, and measure it against the page
budget.

## Inputs

| Input | Notes |
|---|---|
| `<stem>.md` | a brief, never a rubric |

## Produces

`<stem>.pdf` beside the brief.

## Steps

1. `FSA assessment render "<stem>.md"`; for a Vietnamese brief add `--lang vi`.
2. Read the page count it reports against the budget: two A4 pages per hour of
   a timed paper, minimum two. Multi-day work has no budget, but past three
   pages the brief is probably explaining how instead of stating what.
3. Over budget: **cut content** — restated context, paragraphs that could be
   bullets, anything the rubric already covers. Never shrink the font or the
   margins; re-rendering will not fix it.
4. Never render a rubric.

## Done when

The PDF exists and its page count is within budget, reported as "4 of 4 A4
pages for a 2-hour exam".

## Hands off to

`references/assessment/tasks/design/verify.md`.

# Task — Write a group worksheet

The blank form each group fills in during a group lab, so session time goes
into the work and not into drawing tables.

## Inputs

| Input | Notes |
|---|---|
| the lab guide | what each group produces, step by step |
| the approved outline | from `references/material/tasks/propose_outline.md`, often with the lab's |

## Produces

`<subject>_lab_NN_worksheet.html` beside the lab.

## Steps

1. **Outline first.** Without an approved outline for this worksheet, stop and
   run `references/material/tasks/propose_outline.md`.
2. The same head as the lab (`fsa:kind` set to `worksheet`, the theme linked),
   then an `<h1>` naming the lab and a line for the group's name and members.
3. One `<h2>` per output the lab asks for, in the lab's order, with the table
   or list it needs drawn in advance: column headers, empty rows.
4. No instructions beyond "fill in each section"; the lab guide holds the steps.
   No sample answers.
5. Name the worksheet in the lab's **Before You Start**.

## Done when

Every output the lab's steps ask a group for has a place on the sheet, and the
folder still passes `FSA material verify`.

## Hands off to

Nothing.

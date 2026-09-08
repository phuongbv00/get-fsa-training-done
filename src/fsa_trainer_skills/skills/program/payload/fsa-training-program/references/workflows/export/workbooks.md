# Workflow — export the vendor workbook

```bash
FSA program export syllabus \
  --template "Template_Import_Syllabus.xlsx" \
  --syllabus "syllabi/<TOPIC>_Syllabus.md" \
  -o "<TOPIC>_Syllabus.xlsx"
```

The session plan is found beside the syllabus unless `--schedule` names it.

## Step 0 — ask for the template

The vendor form is the customer's property. It is **not** shipped with this
skill and must never be committed to a repository. Ask the user for the path.

It must be `.xlsx`. A `.xls` is a different, closed format this cannot read;
ask the user to open it once and save a `.xlsx` copy.

## What export does

It **edits a copy of the template** rather than building a workbook. The sheets
being populated are rewritten and every other part is copied through untouched,
so the logo, the classification label, the print setup, the data validations and
all the formatting survive. Rebuilding the file with a spreadsheet library loses
them.

Then it renames the placeholder sheets after the topic, removes the form's dead
identity sheet, and asks the reader to recalculate on open.

## It verifies first, and refuses

Sources that do not reconcile are not exported. A workbook that looks official
and states figures disagreeing with each other is worse than no workbook.
`--no-verify` overrides this; say so plainly if you use it.

## What it will not do

- **Invent formatting.** It populates a formatted template and reuses the style
  each cell already has. It cannot create a fill, a border or a number format,
  so a value with nowhere to go has nowhere to go.
- **Grow the sheet.** The session-plan band is a fixed number of rows with the
  summary block immediately below it. A longer plan is refused rather than
  allowed to overwrite the formulas the syllabus reads.

## After exporting

Open the result. The Time Allocation percentages are formulas over the schedule
sheet, so they should show the same figures the syllabus does — if they read
zero, the durations went in as text.

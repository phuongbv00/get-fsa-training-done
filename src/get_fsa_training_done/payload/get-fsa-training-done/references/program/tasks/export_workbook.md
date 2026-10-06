# Task — Export the vendor workbook

Fill a copy of the customer's syllabus form from a verified syllabus.

## Inputs

| Input | Notes |
|---|---|
| `template_path` | the vendor form, **`.xlsx` only**; ask for it — it is the customer's property, never shipped and never committed |
| the syllabus | `syllabi/<TOPIC>_Syllabus.md`; its plan is found beside it |

## Produces

`<TOPIC>_Syllabus.xlsx`.

## Steps

```bash
FSA program export syllabus --template "<Template_Import_Syllabus.xlsx>" \
  --syllabus "syllabi/<TOPIC>_Syllabus.md" -o "<TOPIC>_Syllabus.xlsx"
```

- A `.xls` cannot be read: ask the user to save a `.xlsx` copy.
- Export **edits a copy** of the template: the populated sheets are rewritten
  and every other part is copied through, so logo, classification label, print
  setup and formatting survive. It renames the placeholder sheets, removes the
  form's dead identity sheet, and keeps the summary block in its place below a
  fixed-height session band.
- It verifies first and refuses sources that do not reconcile; `--no-verify`
  overrides, and if you use it say so.
- It cannot invent formatting or grow the sheet: an over-long plan is refused.

## Done when

The workbook opens and its Time Allocation formulas show the same figures as
the syllabus — zeros mean the durations went in as text.

## Hands off to

Nothing.

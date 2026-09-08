# What a programme is made of

Seven files, plus one pair per topic. Every number in the right-hand column is
*derived* from the left — which is why the tooling can check them against each
other, and why none of them should be typed twice.

## Programme level

| File | Holds | Feeds |
|---|---|---|
| `<PROGRAM>_TrainingProgramCurriculum.md` | title, role, and the module table with hours and days | everything: the module codes, the totals, and the length of a training day |
| `<PROGRAM>_MasterSchedule.csv` | one row per module, one `Mark` in its assessment week | the workbook's Master Schedule sheet |
| `<PROGRAM>_DetailedSchedule.csv` | hours per calendar day, per module | the delivery calendar |
| `<PROGRAM>_TopicList.csv` | code, name, module, content group | the topic list sheet |
| `<PROGRAM>_OSTModuleMapping.csv` | outcome standards, and which module delivers each | evidence that every outcome is taught |

## Topic level, one pair per module

| File | Holds |
|---|---|
| `syllabi/<TOPIC>_Syllabus.md` | objectives, outline, time allocation, materials, assessment scheme, delivery principles, authorship |
| `syllabi/<TOPIC>_ScheduleDetail.csv` | one row per activity: unit, chapter, session, content, objectives, delivery type, duration, materials |

## What derives from what

```
module table ──┬─→ every CSV's column layout and row order   (FSA program derive skeleton)
               ├─→ total hours ÷ total days = a training day's length
               └─→ the day and week column counts

session plan ──┬─→ section 8, Time Allocation                (FSA program derive allocation)
               ├─→ the topic's day count
               └─→ every assessment item's count
```

**A programme constant is never invented.** The module count, the totals, the
length of a training day, the number of week and day columns: all of them come
from the sources. If one cannot be derived, the sources disagree — report that
rather than choosing a number.

## The `Training Materials` column

Each session row names the file that serves it. Those files belong to the other
two skills:

| Named file | Produced by |
|---|---|
| `*_quiz_*.csv`, `*_assignment_*.md`, `*_exam_*.md`, rubrics | `fsa-training-assessment` |
| `*_lecture_*.md`, `*_lab_*.md`, handbooks | `fsa-training-material` |

This skill declares that a slot exists, what it weighs and what will fill it. It
never writes the instrument or the lecture. When a finding is really about one
of those, name the skill that owns it.

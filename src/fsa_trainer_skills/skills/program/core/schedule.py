"""The session plan: `<TOPIC>_ScheduleDetail.csv`.

One row per activity, grouped into sessions, grouped into chapters. This is the
document every other number in a syllabus is derived from — the time-allocation
shares, the day count, and the assessment counts all reduce to sums over these
rows, which is why they are derived rather than typed.
"""

from __future__ import annotations

#: Closed list, and the row order of the syllabus's Time Allocation table. The
#: vendor workbook writes these as a fixed block, so both the set and the order
#: are part of the contract.
DELIVERY_TYPES = (
    "Concept/Lecture",
    "Assignment/Lab",
    "Guides/Review",
    "Seminar/Workshop",
    "Class Meeting",
    "Test/Quiz",
    "Exam",
)

TRAINING_FORMAT = "Blended"

#: Fixed and case-sensitive: these become the workbook's column headers.
SCHEDULE_HEADER = (
    "Unit",
    "Training Unit/Chapter",
    "Session",
    "Content",
    "Learning Objectives",
    "Delivery Type",
    "Duration (mins)",
    "Training Format",
    "Training Materials / Logistics & General Notes",
)

MATERIALS_COLUMN = "Training Materials / Logistics & General Notes"
OBJECTIVES_COLUMN = "Learning Objectives"

__all__ = [
    "DELIVERY_TYPES",
    "MATERIALS_COLUMN",
    "OBJECTIVES_COLUMN",
    "SCHEDULE_HEADER",
    "TRAINING_FORMAT",
]

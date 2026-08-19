# Capstone project spec template

A capstone brief describes the *product*. This spec pins down everything about
how the work is organised and judged — team size, how long, how many sprints,
what stack, what the demo looks like, and how an individual's contribution is
separated from their team's.

It exists because these are exactly the things that get referred to and never
defined. A deliverables list that says "nộp trong Sprint 1" without anywhere
defining how many sprints there are, or how long one lasts, cannot be graded
consistently.

Written in the same language as the brief — Vietnamese by default.

---

```markdown
# Project Spec - <Tên dự án>

> **Code:** <LEVEL>_<SUBJ>_PRJ_<seq>
> **Level:** <LEVEL>

## Team size

<Số thành viên mỗi nhóm, và cách chia nhóm.>

## Duration

<Tổng thời lượng, ngày bắt đầu và ngày bảo vệ.>

## Sprints

<Số sprint, độ dài mỗi sprint, và những gì phải nộp ở cuối mỗi sprint.>

## Stack

<Ngôn ngữ, framework, database bắt buộc. Nêu rõ những gì được phép tự chọn.>

## Demo

<Thời lượng buổi bảo vệ, cấu trúc (demo / hỏi đáp), và yêu cầu mỗi thành viên
trình bày phần mình phụ trách.>

## Contribution

<Đóng góp cá nhân được đo bằng gì: commit history, biên bản sprint, phần trình
bày trong buổi bảo vệ. Nêu rõ điểm cá nhân ảnh hưởng thế nào tới điểm cuối.>
```

---

## Required sections

`FSA verify --type capstone_project --spec …` checks that all six are present.
Each corresponds to something the deliverables refer to:

| Section | What refers to it |
|---|---|
| Team size | group deliverables and per-member contribution |
| Duration | the whole schedule |
| Sprints | every "nộp trong Sprint N" line |
| Stack | the source-code deliverable |
| Demo | the final presentation deliverable |
| Contribution | the rubric's individual-contribution task |

## Why contribution is mandatory

Without a task that scores the individual, every member of a team receives the
team's mark regardless of what they did. The verifier treats a rubric with no
contribution task as an error, not a warning.

# Task — Write the module handbook

`00_Study_Guide_Handbook.md`: the first thing a trainee opens, and the only
place that describes the module as a whole.

## Inputs

| Input | Notes |
|---|---|
| `materials_dir` | the module's folder |
| the notes | at least their titles and order |

## Produces

`00_Study_Guide_Handbook.md`. Index `00` is reserved for it.

## Steps

1. Start from `references/material/templates/handbook.md`. It holds: Module Map
   (every note, in order, one line each), How to Use This Handbook, Environment
   Setup (pinned to versions), How to Study This Module, Glossary.
2. **Pin the versions.** Say which versions the notes assume and how to tell
   when something read elsewhere is out of date.
3. **Name the running domain** that the notes share.

## Done when

`FSA material verify "<materials_dir>"` reports no errors for it.

## Hands off to

`references/material/tasks/derive_appendix.md`.

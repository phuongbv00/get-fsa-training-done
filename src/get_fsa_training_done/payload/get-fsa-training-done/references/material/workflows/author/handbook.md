# Workflow — write a module handbook

**Produces:** `00_Study_Guide_Handbook.md`.

Index `00` is reserved for it. It is the first thing a learner opens, and the
only place that describes the module as a whole.

## What it holds

| Section | Holds |
|---|---|
| Module Map | every note, in order, one line each |
| How to Use This Handbook | how the module is meant to be worked through |
| Environment Setup | what to install, pinned to versions |
| How to Study This Module | the study method, and what to do when stuck |
| Glossary | terms the module assumes |

`references/material/templates/handbook.md` is the skeleton.

## Two things worth getting right

**Pin the versions.** A module's notes are written against a stack, and a
learner following a tutorial from a different major version loses hours. Say
which versions the notes assume, and say how to tell when something they read
elsewhere is out of date.

**Name the running domain.** The notes compose if they share one worked example,
and this is where that is introduced.

## Check it

```bash
FSA material verify "<folder>"
```

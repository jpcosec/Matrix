# Pill 07 - Task Granularity and Parallelism

## What

Tasks should be as granular as possible and should expose clear dependencies.

## Why

Granular tasks reduce ambiguity, reduce context contamination, and make parallel execution by different agents feasible.

## How

- Prefer tasks like "delete files 1,2,3" or "extract functions A,B,C into module X".
- Avoid tasks like "clean all legacy".
- Make dependencies explicit on the task board.
- Keep touched files narrow and concrete.

## What For

This allows phased execution, safe delegation, and less architectural drift.

## Applies To

- all tasks under `DESK/tasks/`

## Does Not Apply To

- none; this is a global execution rule for DESK work

## Failure Modes

- one task touches unrelated surfaces
- multiple tasks silently depend on the same unstated architectural assumption

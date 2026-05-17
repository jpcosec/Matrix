# DESK

Temporary execution workspace for rebuilding Matrix on the new proposition-first operational model.

## Purpose

This desk tracks only active implementation scaffolding for Matrix.

- Code is truth.
- Tests prove behavior.
- Specs explain architecture.
- DESK files are temporary working surfaces.
- Resolved tasks must be deleted; history belongs in git.

## Current Direction

Matrix is being rebuilt around:

- `Thing`
- `Relation`
- `Proposition`
- `Fact`
- `LiSpace`
- `WiGame`
- `Context`
- `SearchVector (p_i)`
- `RoutingProjection (r_i)`

The old `UnifiedMatrixEngine` stack is now treated as legacy. Any useful logic should be migrated into the new codebase; everything else should be deleted and preserved only in git history.

## Active Index

- `DESK/PROCEDURE.md`
- `DESK/RITUALS.md`
- `DESK/CONTEXT-PILLS.md`
- `DESK/TASK-SPEC.md`
- `DESK/pills/README.md`
- `DESK/tasks/Board.md`
- `DESK/tasks/task-00-legacy-inventory.md`
- `DESK/tasks/task-01-delete-legacy-tests.md`
- `DESK/tasks/task-02-migrate-useful-legacy-capabilities.md`
- `DESK/tasks/task-03-delete-legacy-runtime.md`

## Authoring Rule

Each task must be executable by an agent that reads only:

1. the task file
2. the task board
3. the listed pills
4. the listed references

If that is not possible, the task is underspecified and must be hardened before implementation.

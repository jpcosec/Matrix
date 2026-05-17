# DESK

Temporary execution workspace for active Matrix implementation work.

## Purpose

DESK exists to coordinate live work without turning temporary scaffolding into permanent architecture.

- Code is truth.
- Tests prove behavior.
- Specs explain architecture.
- DESK files support execution, not long-term architectural storage.
- Resolved task files must be deleted; history belongs in git.

## Scope

Use DESK for:

- working procedure
- task authoring rules
- active task tracking in `DESK/tasks/Board.md`
- task files that are still open

Do not use DESK as the permanent home for architectural decisions. Once a decision stabilizes, it belongs in `docs/`.

## Authoring Rule

Each task must be executable by an agent that reads only:

1. the task file
2. the task board
3. the listed documentation references
4. the listed code references

If that is not possible, the task is underspecified and must be hardened before implementation.

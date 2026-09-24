# task-desk-01 - close stale task and clean Board

## Goal

`DESK/tasks/task-db-04-test-yaml-persistence.md` sits in the tasks folder but references a storage boundary doc that was already added in the latest commit (`c1e8cf1`). The Board shows no active tasks, which means the task is likely resolved but was never cleaned up.

## Objective

Audit `task-db-04`, close it if resolved, and leave the Board honest.

## Non-Goals

- redesigning the DESK workflow
- adding new tasks to the Board (separate task)

## Documentation References

- `DESK/README.md`
- `DESK/PROCEDURE.md`
- `DESK/RITUALS.md`

## References

- `DESK/tasks/task-db-04-test-yaml-persistence.md`
- `DESK/tasks/Board.md`

## Exact Files To Change

- `DESK/tasks/task-db-04-test-yaml-persistence.md` — delete if resolved
- `DESK/tasks/Board.md` — update status

## Files To Avoid Unless Necessary

- any file outside `DESK/`

## Delete / Migrate Decision

- `task-db-04` — delete if resolved, defer if still valid

## End State

No stale task files remain in `DESK/tasks/`. Board accurately reflects active work.

## Exit Criteria

- `ls DESK/tasks/` contains only active task files
- Board references only active tasks

## Suggested Implementation Path

1. Review the exit criteria in `task-db-04` against current code
2. If met: delete the file and remove from Board
3. If not met: move to "Active" on Board

## Validation

- Visual inspection of `DESK/tasks/` and `DESK/tasks/Board.md`

## Failure Modes

- deleting a task that still has valid unfinished work

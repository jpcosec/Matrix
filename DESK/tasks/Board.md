# Task Board

## Active Tasks

- **task-core-01-doc-and-legacy-sync** - clean remaining architectural drift around `Si`, `Oi`, and the stale runtime surfaces; see `DESK/tasks/task-core-01-doc-and-legacy-sync.md`
- **task-storage-01-postgres-compatibility** - define the persistence boundary so the current prototype stays YAML-first while remaining compatible with future Postgres-backed symbol spaces; see `DESK/tasks/task-storage-01-postgres-compatibility.md`

## Deferred / Future

- Future tasks should be split from the active files above only when new scope appears beyond this session backlog.

## Execution Rule

Before starting a task, check:
1. Are the exact files listed?
2. Are the documentation references listed explicitly?
3. Is every touched legacy surface marked `migrate`, `delete`, or `defer`?
4. Is the validation command concrete?
5. Does the task strengthen the new architecture instead of preserving the old one?

If any answer is no, improve the task first.

# Task Board

## Active Tasks

- **task-core-01-doc-and-legacy-sync** - clean remaining architectural drift around `Si`, `Oi`, and the stale runtime surfaces; see `DESK/tasks/task-core-01-doc-and-legacy-sync.md`
- **task-kernel-02-lowering-and-db-spaces** - operationalize `instance` and `equivalent` as kernel lowering primitives over DB-backed symbol spaces; see `DESK/tasks/task-kernel-02-lowering-and-db-spaces.md`
- **task-rel-02-validation-routing-and-identity** - use relation semantics for sense validation, routing hooks, reduction hooks, and equivalence-aware fact identity; see `DESK/tasks/task-rel-02-validation-routing-and-identity.md`
- **task-proto-shrdlu-02-lowering-and-dialog** - turn the separate SHRDLU prototype into a real client of the kernel with lowering, ambiguity, and a tiny execution harness; see `DESK/tasks/task-proto-shrdlu-02-lowering-and-dialog.md`
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

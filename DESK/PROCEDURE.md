# Procedure

This file captures the working procedure for Matrix rebuild work.

## Session Initialization Ritual

Before implementation starts:

```text
1. READ BOARD      -> Read DESK/tasks/Board.md
2. CHECK LEGACY    -> Read the active legacy inventory task
3. CHECK STATUS    -> Inspect current code and tests
4. PICK SCOPE      -> Choose one task with explicit files and validation
```

## Completion Ritual

When a task is done:

```text
1. VERIFY   -> Update or replace the relevant tests
2. TEST     -> Run the required suite(s)
3. SPEC     -> Update docs if architecture changed
4. CLEAN    -> Remove stale task artifacts when resolved
5. BOARD    -> Update DESK/tasks/Board.md
6. COMMIT   -> Atomic commit only if requested and after closure
```

## Truth Hierarchy

- Code is truth.
- Tests prove behavior.
- Specs explain architecture.
- DESK tracks active implementation work only.

## What Not To Do

- Do not keep legacy modules alive only because tests still point at them.
- Do not move old abstractions unchanged into the new codebase.
- Do not let temporary compatibility shims become permanent architecture.
- Do not keep resolved tasks in `DESK/tasks/`.

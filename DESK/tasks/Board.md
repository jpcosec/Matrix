# Task Board

## Active Tasks

| Task | Domain | Objective | Priority | Pills |
|------|--------|-----------|----------|-------|
| task-02f | runtime/migration | Decide whether visualization export survives and migrate it only if still needed | p1 | pill-04, pill-07 |

## Deferred / Future

- **Si redesign** — German-named dataclass states per pill-06
- **Oi handling** — absorb into Fact metadata per pill-05
- **New ingestion CLI** — s-expression based, replacing old TKMOrchestrator direction

## Execution Rule

Before starting a task, check:
1. Are the exact files listed?
2. Are the pills listed explicitly?
3. Is every touched legacy surface marked `migrate`, `delete`, or `defer`?
4. Is the validation command concrete?
5. Does the task strengthen the new architecture instead of preserving the old one?

If any answer is no, improve the task first.

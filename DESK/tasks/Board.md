# Task Board

## Active Tasks

| Task | Domain | Objective | Priority | Documentation |
|------|--------|-----------|----------|---------------|
| task-db-02 | routing | Formalize and test multi-Wi routing semantics | p0 | `docs/architecture.md`, `docs/operations.md` |
| task-db-03 | operations | Formalize and test the contract of query and projection operations | p0 | `docs/operations.md`, `docs/data_models.md` |
| task-db-04 | serialization | Harden YAML persistence through round-trip tests and schema checks | p1 | `docs/canonical_forms_and_ingestion.md`, `docs/data_models.md` |

## Deferred / Future

- **Si redesign** — see `docs/proposition_first_architecture.md`
- **Oi handling** — see `docs/proposition_first_architecture.md`
- **New ingestion CLI** — see `docs/canonical_forms_and_ingestion.md`
- **Postgres compatibility path** — stay full YAML for the prototype, but keep future storage work compatible with Postgres and graph-oriented extensions

## Execution Rule

Before starting a task, check:
1. Are the exact files listed?
2. Are the documentation references listed explicitly?
3. Is every touched legacy surface marked `migrate`, `delete`, or `defer`?
4. Is the validation command concrete?
5. Does the task strengthen the new architecture instead of preserving the old one?

If any answer is no, improve the task first.

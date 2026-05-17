# Task Board

## Active Tasks

Only active tasks belong here.

`task-00` closes the inventory phase. No downstream task should be executed until `task-00` is explicitly complete.

| Task | Domain | Objective | Priority | Depends On | Pills | Completion Gate |
|------|--------|-----------|----------|------------|-------|-----------------|
| task-00 | audit/architecture | Inventory every legacy runtime and test surface as migrate/delete/defer | p0 | none | pill-04, pill-07 | COMPLETE |
| task-01 | tests/cleanup | Delete legacy test files that only preserve old runtime behavior | p0 | task-00 | pill-04, pill-07 | COMPLETE |
| task-02a | runtime/migration | Extract boolean matrix multiplication from legacy runtime into the new model | p0 | task-00 | pill-04, pill-07 | COMPLETE |
| task-02b | runtime/migration | Rebuild dimensional collapse on the new model | p0 | task-00, task-02a | pill-01, pill-04, pill-07 | COMPLETE |
| task-02c | runtime/migration | Rebuild recursive routing on top of `Context` and `RoutingProjection` | p0 | task-00, task-02a | pill-03, pill-04, pill-07 | COMPLETE |
| task-02d | runtime/migration | Rebuild information energy on top of the new model | p0 | task-00 | pill-04, pill-07 | COMPLETE |
| task-02e | runtime/migration | Redesign status evaluation around the new `Si` model | p0 | task-00 | pill-04, pill-06, pill-07 | COMPLETE |
| task-02f | runtime/migration | Decide whether visualization export survives and migrate it only if still needed | p1 | task-00 | pill-04, pill-07 | TODO |
| task-03a | runtime/deletion | Delete legacy tests after migrated replacements exist where needed | p0 | task-01, task-02b, task-02c, task-02d, task-02e | pill-04, pill-07 | TODO |
| task-03b | runtime/deletion | Delete `unified_engine.py` and `unified_engine_core/` after migrations land | p0 | task-02a, task-02b, task-02c, task-02d, task-02e, task-02f | pill-04, pill-07 | TODO |
| task-03c | runtime/deletion | Delete remaining old runtime modules (`matrix_engine`, `boolean_matrix_engine`, `context_composition`, `subcontext_routing`, `multivalued_engine`) | p0 | task-00 | pill-04, pill-07 | TODO |
| task-03d | runtime/deletion | Delete or rewrite `tkm_orchestrator.py` after the new ingestion direction is defined | p1 | task-00 | pill-02, pill-04, pill-07 | TODO |

## Execution Rule

Before starting a task, check:

1. Are the exact files listed?
2. Are the pills listed explicitly?
3. Is every touched legacy surface marked `migrate`, `delete`, or `defer`?
4. Is the validation command concrete?
5. Does the task strengthen the new architecture instead of preserving the old one?

If any answer is no, improve the task first.

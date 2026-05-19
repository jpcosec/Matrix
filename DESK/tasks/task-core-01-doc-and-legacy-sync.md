# Task: task-core-01-doc-and-legacy-sync

## Goal

Close the remaining documentation and terminology drift so the stable architecture, runtime surface, and legacy cleanup direction all tell the same story.

## Objective

Synchronize the stable docs and public README around the active proposition-first runtime, remove residual `Oi` references, and harden the documented direction for the future `Si` redesign.

## Non-Goals

- new runtime features
- propositional kernel execution
- prototype package work

## Documentation References

- `docs/proposition_first_architecture.md`
- `docs/canonical_forms_and_ingestion.md`
- `docs/operations.md`
- `docs/architecture.md`
- `docs/data_models.md`

## References

- `DESK/tasks/Board.md`
- `README.md`
- `docs/README.md`

## Exact Files To Change

- `README.md`
- `docs/README.md`
- `docs/architecture.md`
- `docs/concepts.md`
- `docs/data_models.md`
- `docs/proposition_first_architecture.md`

## Files To Avoid Unless Necessary

- runtime code under `src/`
- prototype packages

## Delete / Migrate Decision

- residual `Oi` terminology: delete
- stale missing `cli.py` narrative: delete
- future `Si` redesign direction: keep but clarify as planned work

## End State

Stable docs describe the real runtime surface, do not point at missing entrypoints, and do not preserve old matrix layers by wording drift.

## Exit Criteria

- no stale `cli.py` quick-start remains
- no architectural doc preserves `Oi` as active structure
- `Si` redesign remains explicitly future-facing

## Suggested Implementation Path

1. Audit all stable docs for stale runtime names.
2. Remove or rewrite `Oi` drift.
3. Rewrite README runtime entrypoints around what exists now.
4. Align docs index and quick verification commands.

## Validation

- `pytest`
- manual read-through of `README.md` and `docs/README.md`

## Failure Modes

- fixing wording in one doc while leaving contradictions elsewhere
- keeping obsolete runtime names to preserve history instead of clarity

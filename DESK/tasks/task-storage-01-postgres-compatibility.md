# Task: task-storage-01-postgres-compatibility

## Goal

Keep the current prototype YAML-first while making sure the symbol/kernel direction remains compatible with a future Postgres-backed persistence layer.

## Objective

Define the storage boundary, serialization invariants, and normalization assumptions required so future Postgres symbol spaces can support the same kernel and Wi semantics.

## Non-Goals

- implementing Postgres
- replacing YAML now
- prototype package work

## Documentation References

- `docs/data_models.md`
- `docs/kernel_symbol_policy.md`
- `docs/canonical_forms_and_ingestion.md`

## References

- `DESK/tasks/Board.md`
- `schemas/`
- `examples/`

## Exact Files To Change

- `docs/storage_boundary.md`
- `docs/data_models.md`
- `docs/README.md`

## Files To Avoid Unless Necessary

- runtime code
- prototype packages

## Delete / Migrate Decision

- implicit storage assumptions: migrate into explicit storage-boundary docs
- YAML-first prototype mode: keep
- direct Postgres implementation: defer

## End State

There is a documented storage boundary that preserves compatibility between the current YAML prototype and future Postgres-backed symbol spaces.

## Exit Criteria

- storage invariants are explicit
- symbol normalization expectations are explicit
- docs state clearly what must stay stable across storage backends

## Suggested Implementation Path

1. Define the storage boundary and invariants.
2. State what is canonical and what is backend-specific.
3. Update docs index and relevant model docs.

## Validation

- manual doc review

## Failure Modes

- documenting storage shape without tying it to kernel semantics

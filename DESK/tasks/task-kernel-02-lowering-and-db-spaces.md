# Task: task-kernel-02-lowering-and-db-spaces

## Goal

Make `instance` and `equivalent` truly operational as kernel primitives tied to normalization and future database-backed symbol spaces.

## Objective

Implement typed assertion lowering for `instance` and `equivalent`, and define how kernel symbols map to classes, aliases, and normalization domains backed by persistence layers.

## Non-Goals

- full Postgres implementation
- propositional rewrite engine
- prototype dialogue execution

## Documentation References

- `docs/kernel_symbol_policy.md`
- `docs/data_models.md`
- `docs/rebuild_and_migration_policy.md`

## References

- `DESK/tasks/task-runtime-02-s-expression-authoring-surface.md`
- `src/operational_model/kernel/symbol_policy.py`

## Exact Files To Change

- `src/operational_model/kernel/typed_assertions.py`
- `src/operational_model/kernel/symbol_spaces.py`
- `src/operational_model/kernel/__init__.py`
- `tests/test_typed_assertions.py`
- `docs/kernel_symbol_policy.md`

## Files To Avoid Unless Necessary

- prototype packages
- unrelated Wi routing code

## Delete / Migrate Decision

- `instance` and `equivalent` as documented-only semantics: migrate into code
- DB normalization assumptions hidden in conversation: migrate into explicit symbol-space policy

## End State

The kernel can lower and operationalize typed assertions and equivalence assertions over a declared symbol-space model.

## Exit Criteria

- `instance` and `equivalent` execute as kernel operations
- symbol-space policy is explicit and test-covered
- future DB mapping points are clear even if not fully implemented

## Suggested Implementation Path

1. Define symbol-space model.
2. Implement typed assertion handling.
3. Implement equivalence normalization hooks.
4. Add tests and docs.

## Validation

- `pytest tests/test_typed_assertions.py`

## Failure Modes

- treating DB-backed symbol spaces as storage only instead of semantic normalization domains

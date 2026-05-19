# Task: task-runtime-02-s-expression-authoring-surface

## Goal

Extend the canonical s-expression runtime from fact assertion into actual authoring of the operational model.

## Objective

Add canonical forms for creating symbols, relations, `LiSpace`, and `WiGame` structures directly through the runtime, and add the first direct `(R a b)` ingestor into proposition-first runtime objects.

## Non-Goals

- full CLI productization
- propositional connective execution
- DB-backed storage

## Documentation References

- `docs/canonical_forms_and_ingestion.md`
- `docs/operations.md`
- `docs/data_models.md`

## References

- `DESK/tasks/Board.md`
- `src/operational_model/system/s_expression_runtime.py`
- `src/operational_model/core/`

## Exact Files To Change

- `src/operational_model/system/s_expression_runtime.py`
- `src/operational_model/system/operation_results.py`
- `tests/test_s_expression_runtime.py`
- `docs/canonical_forms_and_ingestion.md`
- `docs/operations.md`

## Files To Avoid Unless Necessary

- prototype packages
- routing modules beyond minimal registration hooks

## Delete / Migrate Decision

- YAML-only authoring dependence: migrate toward runtime authoring forms
- missing ingestion path from `(R a b)` text to runtime objects: migrate into the active runtime

## End State

The runtime can author the core registries and local games directly from canonical s-expressions.

## Exit Criteria

- symbols and relations can be created through runtime forms
- `LiSpace` and `WiGame` can be authored through runtime forms
- direct proposition ingestion into runtime objects is test-covered

## Suggested Implementation Path

1. Add symbol/relation authoring forms.
2. Add Li/Wi authoring forms.
3. Add direct proposition ingestion and validation.
4. Update tests and docs.

## Validation

- `pytest tests/test_s_expression_runtime.py`

## Failure Modes

- reintroducing non-canonical external text forms
- silently mutating global registries without stable result payloads

# task-db-03 - formalize operations

## Goal

Define the allowed operational surface of the prototype so that queries and projections have a stable contract.

## Objective

Specify and test the expected inputs, outputs, and invariants of operations such as local query, subject projection, and cross-search.

## Non-Goals

- building a network API
- adding database-backed query execution
- redesigning the full domain model

## Documentation References

- `docs/operations.md`
- `docs/data_models.md`
- `docs/proposition_first_architecture.md`
- `docs/rebuild_and_migration_policy.md`

## References

- `src/operational_model/system/logical_system.py`
- `src/operational_model/system/logical_system_queries.py`
- `src/operational_model/system/wi_game_queries.py`
- `src/operational_model/routing/search_vector.py`
- `tests/test_operational_model.py`

## Exact Files To Change

- `src/operational_model/system/logical_system.py`
- `src/operational_model/system/logical_system_queries.py`
- `src/operational_model/system/wi_game_queries.py`
- `tests/test_operational_model.py`
- `tests/test_recursive_routing.py` if contracts overlap
- `docs/operations.md`

## Files To Avoid Unless Necessary

- `src/unified_engine.py`
- `src/matrix_engine.py`
- `src/tkm_orchestrator.py`

## Delete / Migrate Decision

- `src/operational_model/system/**` -> migrate
- `src/operational_model/routing/search_vector.py` -> migrate
- legacy query helpers -> defer

## End State

The prototype exposes a small, explicit set of supported operations with stable return shapes and tests that prove them.

## Exit Criteria

- each supported operation has a documented contract
- tests cover nominal and boundary cases
- the runtime does not promise unsupported operations implicitly

## Suggested Implementation Path

1. Enumerate the supported operations already present in code.
2. Freeze the desired contract of each one.
3. Add or tighten tests before broadening implementation.
4. Refactor return shapes or validation only where the contract requires it.

## Validation

- `pytest tests/test_operational_model.py`
- `pytest tests/test_recursive_routing.py`
- `pytest`

## Failure Modes

- operations remain example-driven instead of contract-driven
- return shapes change silently across tasks
- task expands into persistence or API design

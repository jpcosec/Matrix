# task-db-01 - formalize Wi algebra

## Goal

Turn the current relation flags and Wi-level behavior into an explicit algebraic contract instead of leaving them as passive metadata.

## Objective

Define what the current system means by relation properties such as commutativity, associativity, transitivity, and distributivity, and add executable tests for the parts that the Python prototype already supports.

## Non-Goals

- building a persistent database backend
- redesigning `Si`
- introducing a new ingestion layer
- implementing every possible algebraic operation in one pass

## Documentation References

- `docs/proposition_first_architecture.md`
- `docs/data_models.md`
- `docs/operations.md`
- `docs/rebuild_and_migration_policy.md`

## References

- `src/operational_model/core/relation.py`
- `src/operational_model/core/proposition.py`
- `src/operational_model/system/wigame.py`
- `tests/test_operational_model.py`

## Exact Files To Change

- `src/operational_model/core/relation.py`
- `src/operational_model/system/wigame.py`
- `src/operational_model/system/wi_game_queries.py`
- `tests/test_operational_model.py`
- `docs/operations.md` only if the supported algebra changes materially

## Files To Avoid Unless Necessary

- `src/unified_engine.py`
- `src/boolean_matrix_engine.py`
- `src/context_composition.py`
- `src/subcontext_routing.py`
- `src/tkm_orchestrator.py`

## Delete / Migrate Decision

- `src/operational_model/core/relation.py` -> migrate
- `src/operational_model/system/wigame.py` -> migrate
- legacy runtime files -> defer

## End State

The prototype has a clear statement of which algebraic properties are represented only as declarations, which ones affect behavior, and which ones are covered by tests.

## Exit Criteria

- relation-property semantics are written down in code or docs where the implementation needs them
- tests prove the currently supported behavior
- unsupported algebraic behavior is not implied accidentally

## Suggested Implementation Path

1. Audit the existing use of `Relation` flags.
2. Decide which flags are descriptive only and which ones must affect behavior now.
3. Add the smallest possible behavior or validation needed for the supported subset.
4. Add focused tests around those semantics.
5. Update docs only if implementation semantics become more explicit.

## Validation

- `pytest tests/test_operational_model.py`
- `pytest`

## Failure Modes

- flags remain undocumented but appear authoritative
- tests encode algebra that the runtime does not actually implement
- task grows into a full theorem-prover instead of clarifying the prototype contract

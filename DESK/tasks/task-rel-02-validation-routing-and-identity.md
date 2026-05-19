# Task: task-rel-02-validation-routing-and-identity

## Goal

Use relation semantics for more than inference by making them participate in sense validation, routing, reduction, and fact identity.

## Objective

Extend relation semantics so they can inform proposition admissibility, sense diagnostics, dimensional reductions, context routing decisions, and equivalence-aware fact identity such as `(R a b) == (R b a)` for commutative relations.

## Non-Goals

- full SixVi evaluator
- full propositional kernel execution
- prototype package changes

## Documentation References

- `docs/data_models.md`
- `docs/proposition_first_architecture.md`
- `docs/kernel_symbol_policy.md`

## References

- `DESK/tasks/task-rel-01-relation-semantics.md`
- `src/operational_model/core/relation.py`
- `src/operational_model/system/logical_system_algebra.py`

## Exact Files To Change

- `src/operational_model/core/relations/relation_algebra.py`
- `src/operational_model/system/wi_game_queries.py`
- `src/operational_model/routing/`
- `tests/test_relation_identity.py`
- `tests/test_relation_validation.py`

## Files To Avoid Unless Necessary

- prototype packages
- README/doc sync task surfaces

## Delete / Migrate Decision

- relation semantics used only for inference: migrate into validation and identity logic
- fact identity based only on exact coordinate equality: delete by strengthening with relation semantics where justified

## End State

Relation semantics inform not only inference but also validation, equivalence, and routing-facing decisions.

## Exit Criteria

- commutative fact identity is test-covered
- relation semantics affect validation behavior in at least one explicit path
- routing/reduction hooks are represented even if still minimal

## Suggested Implementation Path

1. Add fact-equivalence helpers.
2. Add validation hooks that consult relation semantics.
3. Expose routing/reduction hook points.
4. Add focused tests.

## Validation

- `pytest tests/test_relation_identity.py tests/test_relation_validation.py`

## Failure Modes

- using semantics for identity in ways that collapse distinct facts incorrectly

# task-db-02 - formalize multi-Wi routing

## Goal

Make routing across more than one `WiGame` a specified and testable system behavior rather than a loosely implied composition.

## Objective

Define the semantics of routing across multiple `WiGame` spaces and add tests that prove the expected behavior for composition, projection, and edge cases.

## Non-Goals

- replacing the routing model with a graph database
- adding persistence beyond current YAML serialization
- redesigning all context concepts at once

## Documentation References

- `docs/proposition_first_architecture.md`
- `docs/architecture.md`
- `docs/operations.md`
- `docs/rebuild_and_migration_policy.md`

## References

- `src/operational_model/routing/context.py`
- `src/operational_model/routing/context_route.py`
- `src/operational_model/routing/routing_projection.py`
- `src/operational_model/system/logical_system.py`
- `src/operational_model/system/logical_system_queries.py`
- `tests/test_recursive_routing.py`

## Exact Files To Change

- `src/operational_model/routing/routing_projection.py`
- `src/operational_model/system/logical_system.py`
- `src/operational_model/system/logical_system_queries.py`
- `tests/test_recursive_routing.py`
- `tests/test_operational_model.py` if shared examples belong there
- `docs/operations.md` if the routing contract becomes more explicit

## Files To Avoid Unless Necessary

- `src/unified_engine.py`
- `src/subcontext_routing.py`
- `src/context_composition.py`
- `src/tkm_orchestrator.py`

## Delete / Migrate Decision

- `src/operational_model/routing/**` -> migrate
- `src/operational_model/system/logical_system*.py` -> migrate
- legacy routing modules -> defer

## End State

Multi-Wi routing has explicit semantics for at least one-hop and multi-hop scenarios, with tests that show what is preserved, intersected, or dropped during traversal.

## Exit Criteria

- multi-Wi routing behavior is encoded in tests
- composition and projection rules are explicit
- edge cases such as empty projections or partial matches are covered

## Suggested Implementation Path

1. Inventory the current routing behavior exposed by `cross_search` and projection helpers.
2. Define the intended multi-hop semantics before expanding code.
3. Add executable tests for one-hop, two-hop, and failure-path cases.
4. Tighten implementation only where tests show ambiguity.

## Validation

- `pytest tests/test_recursive_routing.py`
- `pytest`

## Failure Modes

- routing semantics stay implicit in examples only
- tests cover only happy paths
- task drifts into persistence or storage concerns

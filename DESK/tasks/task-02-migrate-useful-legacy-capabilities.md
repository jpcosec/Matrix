# task-02 - Migrate Useful Legacy Capabilities

## Goal

Extract only the useful parts of the legacy runtime into the new operational model.

## Objective

Reimplement the algorithmic pieces worth keeping without preserving the old container architecture.

## Non-Goals

- Do not keep `UnifiedMatrixEngine` as a permanent compatibility layer.
- Do not migrate `Oi` as a matrix; carry its intent through fact metadata if needed.

## Pills Required

- `pill-01-proposition-first-ontology.md`
- `pill-03-context-vs-wigame.md`
- `pill-04-legacy-migration-policy.md`
- `pill-05-fact-observation-vs-oi.md`
- `pill-06-sense-state-redesign.md`
- `pill-07-task-granularity-and-parallelism.md`

## References

- `src/unified_engine.py`
- `src/operational_model/**`
- `DESK/tasks/task-00-legacy-inventory.md`

## Exact Files To Change

- `src/operational_model/**`
- any new modules needed for migrated algorithms
- `DESK/tasks/Board.md`

## Files To Avoid Unless Necessary

- legacy tests slated for deletion

## Delete / Migrate Decision

### Migrate candidates

| Capability | Decision | Destination idea |
|---|---|---|
| boolean matrix multiplication | migrate | matrix utilities in the new model |
| dimensional collapse | migrate | new matrix/routing layer |
| recursive bridge routing | migrate | new `Context`/`RoutingProjection` layer |
| information energy | migrate | analysis layer on top of `WiGame` |
| status evaluation | migrate | new `Si` state model |
| visualization export | optional migrate | dedicated visualization package |

### Explicit non-migrations

| Capability | Decision | Reason |
|---|---|---|
| `Oi` matrix | delete as matrix | better represented on `Fact` metadata |
| legacy schema loader shape | replace | should match the new model directly |

## End State

Useful behavior survives in the new codebase, free of the old architecture.

## Exit Criteria

- Migrated capabilities exist in new modules.
- New tests cover migrated behavior.
- No migrated feature depends on `UnifiedMatrixEngine`.

## Suggested Implementation Path

1. Execute one migration subtask at a time.
2. Write new focused tests.
3. Bind the algorithm to the new model.
4. Delete the legacy source once nothing active uses it.

## Validation

- focused pytest commands for each migrated capability

## Failure Modes

- Copying old code without reshaping it to the new model.
- Preserving old naming and ontology by inertia.

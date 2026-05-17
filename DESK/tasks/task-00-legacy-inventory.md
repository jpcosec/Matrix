# task-00 - Legacy Inventory

## Goal

Create a hard inventory of what in Matrix is legacy so deletion and migration can be done deliberately.

## Objective

Mark each known legacy runtime and test surface as `migrate`, `delete`, or `defer`, with a short reason.

This task closes the inventory phase only when the mapping is exhaustive for the active Python codebase surface.

## Non-Goals

- Do not implement migration in this task.
- Do not repair legacy semantics beyond what is needed to inspect them.

## Pills Required

- `pill-04-legacy-migration-policy.md`
- `pill-07-task-granularity-and-parallelism.md`

## References

- `cli.py`
- `setup.py`
- `src/unified_engine.py`
- `src/unified_engine_core/`
- `src/operational_model/**`
- `src/__init__.py`
- `src/tkm_orchestrator.py`
- `src/matrix_engine.py`
- `src/boolean_matrix_engine.py`
- `src/context_composition.py`
- `src/subcontext_routing.py`
- `src/multivalued_engine.py`
- `tests/test_operational_model.py`
- `tests/test_tkm_roundtrip_suite.py`
- `tests/test_tkm_implementation.py`
- `tests/test_wikipedia_solar_system.py`
- `tests/test_tkm_atom_map.py`
- `tests/test_whitepaper_ingestion.py`
- `tests/test_dimensional_collapse.py`
- `tests/test_tkm_orchestration.py`
- `tests/test_unified.py`
- `tests/test_matrix_engine.py`

## Exact Files To Change

- `DESK/tasks/task-00-legacy-inventory.md`
- `DESK/tasks/Board.md`

## Files To Avoid Unless Necessary

- `src/operational_model/**`

## Delete / Migrate Decision

### Root Python surfaces

| Surface | Decision | Reason |
|---|---|---|
| `cli.py` | defer | CLI may survive, but must be rebound to the new runtime later. |
| `setup.py` | defer | Packaging surface remains relevant independent of legacy runtime removal. |

### New runtime surfaces

| Surface | Decision | Reason |
|---|---|---|
| `src/__init__.py` | keep | Public export surface for the new codebase. |
| `src/operational_model/__init__.py` | keep | Public API for the proposition-first runtime. |
| `src/operational_model/_ids.py` | keep | Shared utility for the new runtime. |
| `src/operational_model/core/__init__.py` | keep | New-model package surface. |
| `src/operational_model/core/name.py` | keep | New-model domain primitive. |
| `src/operational_model/core/symbol.py` | keep | New-model domain primitive. |
| `src/operational_model/core/thing.py` | keep | New-model domain primitive. |
| `src/operational_model/core/relation.py` | keep | New-model domain primitive. |
| `src/operational_model/core/proposition.py` | keep | Core proposition primitive. |
| `src/operational_model/core/fact.py` | keep | Core fact primitive. |
| `src/operational_model/core/li_space.py` | keep | Core indexing primitive. |
| `src/operational_model/core/truth_value.py` | keep | New-model truth representation. |
| `src/operational_model/core/sense_value.py` | keep for now | Transitional sense state surface until dataclass redesign lands. |
| `src/operational_model/core/route_target_kind.py` | keep | New-model routing enum. |
| `src/operational_model/matrices/__init__.py` | keep | New-model package surface. |
| `src/operational_model/matrices/boolean_matrix.py` | keep | Matrix base for the new model. |
| `src/operational_model/matrices/vi_matrix.py` | keep | New-model truth matrix. |
| `src/operational_model/matrices/si_matrix.py` | keep | New-model sense matrix pending redesign. |
| `src/operational_model/routing/__init__.py` | keep | New-model package surface. |
| `src/operational_model/routing/context.py` | keep | New-model routing node. |
| `src/operational_model/routing/context_route.py` | keep | New-model routing edge. |
| `src/operational_model/routing/routing_projection.py` | keep | New-model `r_i` primitive. |
| `src/operational_model/routing/search_vector.py` | keep | New-model `p_i` primitive. |
| `src/operational_model/system/__init__.py` | keep | New-model package surface. |
| `src/operational_model/system/wigame.py` | keep | New-model aggregate root. |
| `src/operational_model/system/wi_game_registry.py` | keep | New-model helper split. |
| `src/operational_model/system/wi_game_queries.py` | keep | New-model helper split. |
| `src/operational_model/system/wi_game_serialization.py` | keep | New-model helper split. |
| `src/operational_model/system/logical_system.py` | keep | New-model orchestration root. |
| `src/operational_model/system/logical_system_registry.py` | keep | New-model helper split. |
| `src/operational_model/system/logical_system_queries.py` | keep | New-model helper split. |

### Legacy runtime surfaces

| Surface | Decision | Reason |
|---|---|---|
| `src/unified_engine.py` | migrate then delete | Contains mixed useful algorithms and obsolete architecture. |
| `src/unified_engine_core/` | defer | Temporary extraction while migration is in progress. |
| `src/tkm_orchestrator.py` | defer | Depends on legacy runtime and should be revisited after runtime migration. |
| `src/matrix_engine.py` | delete | Object/property model from the old stack. |
| `src/boolean_matrix_engine.py` | inspect then likely delete | May contain reusable matrix helpers, but architecture is legacy. |
| `src/context_composition.py` | inspect then likely migrate/delete | Concept overlaps with new `Context`/`r_i` model. |
| `src/subcontext_routing.py` | inspect then likely migrate/delete | Routing concept overlaps with new `Context` model. |
| `src/multivalued_engine.py` | inspect then likely delete | Legacy runtime branch not aligned to the new base. |

### Transitional extraction surfaces

| Surface | Decision | Reason |
|---|---|---|
| `src/unified_engine_core/__init__.py` | defer | Transitional package while `unified_engine.py` is dismantled. |
| `src/unified_engine_core/truth_value.py` | defer | Likely superseded by new truth model or folded into migrated algorithms. |
| `src/unified_engine_core/symbol_registry.py` | defer | Transitional extraction from the legacy runtime. |
| `src/unified_engine_core/context.py` | defer | Legacy context shape, not the new `Context`. |
| `src/unified_engine_core/bridge.py` | defer | Legacy bridge shape, not the new routing projection layer. |

### Tests

| Surface | Decision | Reason |
|---|---|---|
| `tests/__init__.py` | keep | Neutral test package marker. |
| `tests/test_operational_model.py` | keep | Tests the new codebase. |
| `tests/test_tkm_roundtrip_suite.py` | delete or rewrite | Preserves legacy engine semantics. |
| `tests/test_tkm_implementation.py` | delete or rewrite | Preserves legacy hierarchical status behavior. |
| `tests/test_wikipedia_solar_system.py` | delete or rewrite | Legacy engine acceptance test. |
| `tests/test_tkm_atom_map.py` | delete | Pure legacy runtime coverage. |
| `tests/test_whitepaper_ingestion.py` | delete | Legacy runtime coverage. |
| `tests/test_dimensional_collapse.py` | migrate | Keep only the algorithmic intent in new tests. |
| `tests/test_tkm_orchestration.py` | delete | Depends on legacy orchestration. |
| `tests/test_unified.py` | delete | Broken legacy API coverage. |
| `tests/test_matrix_engine.py` | delete | Old engine coverage. |

## Exhaustive Current Mapping

### Keep now

- `cli.py`
- `setup.py`
- `src/__init__.py`
- `src/operational_model/__init__.py`
- `src/operational_model/_ids.py`
- `src/operational_model/core/__init__.py`
- `src/operational_model/core/name.py`
- `src/operational_model/core/symbol.py`
- `src/operational_model/core/thing.py`
- `src/operational_model/core/relation.py`
- `src/operational_model/core/proposition.py`
- `src/operational_model/core/fact.py`
- `src/operational_model/core/li_space.py`
- `src/operational_model/core/truth_value.py`
- `src/operational_model/core/sense_value.py`
- `src/operational_model/core/route_target_kind.py`
- `src/operational_model/matrices/__init__.py`
- `src/operational_model/matrices/boolean_matrix.py`
- `src/operational_model/matrices/vi_matrix.py`
- `src/operational_model/matrices/si_matrix.py`
- `src/operational_model/routing/__init__.py`
- `src/operational_model/routing/context.py`
- `src/operational_model/routing/context_route.py`
- `src/operational_model/routing/routing_projection.py`
- `src/operational_model/routing/search_vector.py`
- `src/operational_model/system/__init__.py`
- `src/operational_model/system/wigame.py`
- `src/operational_model/system/wi_game_registry.py`
- `src/operational_model/system/wi_game_queries.py`
- `src/operational_model/system/wi_game_serialization.py`
- `src/operational_model/system/logical_system.py`
- `src/operational_model/system/logical_system_registry.py`
- `src/operational_model/system/logical_system_queries.py`
- `tests/__init__.py`
- `tests/test_operational_model.py`

### Defer temporarily

- `src/unified_engine_core/__init__.py`
- `src/unified_engine_core/truth_value.py`
- `src/unified_engine_core/symbol_registry.py`
- `src/unified_engine_core/context.py`
- `src/unified_engine_core/bridge.py`
- `src/tkm_orchestrator.py`

### Migrate then delete

- `src/unified_engine.py`

### Inspect for selective migration then likely delete

- `src/boolean_matrix_engine.py`
- `src/context_composition.py`
- `src/subcontext_routing.py`
- `src/multivalued_engine.py`

### Delete

- `src/matrix_engine.py`
- `tests/test_tkm_roundtrip_suite.py`
- `tests/test_tkm_implementation.py`
- `tests/test_wikipedia_solar_system.py`
- `tests/test_tkm_atom_map.py`
- `tests/test_whitepaper_ingestion.py`
- `tests/test_tkm_orchestration.py`
- `tests/test_unified.py`
- `tests/test_matrix_engine.py`

### Migrate test intent then delete original

- `tests/test_dimensional_collapse.py`

## End State

A stable inventory exists that makes future deletion and migration tasks mechanical.

## Exit Criteria

- All known legacy runtime surfaces are classified.
- All known legacy test surfaces are classified.
- Every current Python file in the active root, `src/`, and `tests/` surfaces appears in this inventory.
- Follow-up tasks reflect that classification.

## Suggested Implementation Path

1. Audit every current Python file in root, `src/`, and `tests/`.
2. Separate new surfaces from transitional and legacy surfaces.
3. Record file-level classification tables.
4. Update the task board only after the mapping is exhaustive.

## Validation

- Read `DESK/tasks/task-00-legacy-inventory.md`
- Confirm every current Python file is listed exactly once in the exhaustive mapping
- Confirm every listed legacy surface has a decision and reason

## Failure Modes

- Calling something "defer" when it should be deleted.
- Keeping legacy tests only because they are already written.
- Closing the inventory phase while some files remain unmapped.

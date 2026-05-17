# Refactor Rules Matrix

Legend: `OK` satisfies the current heuristic, `FAIL` violates it. `DupRisk` and `Quality` are manual triage helpers used to organize refactoring work.

Rule columns map directly to the coding standard: module docstrings, class docstrings, function docstrings, folder size, file size, one class per file, max two methods per class, max eight lines per function, plus duplication risk and overall quality.

## Source Files

| File | Lines | MDoc | CDoc | FDoc | Dir<=5 | File<=80 | 1Class/File | <=2Meth/Class | <=8LineFn | DupRisk | Quality |
|---|---|---|---|---|---|---|---|---|---|---|---|
| src/__init__.py | 45 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/boolean_matrix_engine.py | 387 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | HIGH | HIGH |
| src/context_composition.py | 369 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | HIGH | HIGH |
| src/matrix_engine.py | 142 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | HIGH | HIGH |
| src/multivalued_engine.py | 309 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | HIGH | HIGH |
| src/operational_model/__init__.py | 39 | OK | OK | OK | OK | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/_ids.py | 11 | OK | OK | OK | OK | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/__init__.py | 25 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/fact.py | 20 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/li_space.py | 28 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/name.py | 13 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/proposition.py | 23 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/relation.py | 19 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/route_target_kind.py | 12 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/sense_value.py | 13 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/symbol.py | 31 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/thing.py | 32 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/core/truth_value.py | 13 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/matrices/__init__.py | 7 | OK | OK | OK | OK | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/matrices/boolean_matrix.py | 106 | OK | OK | OK | OK | FAIL | OK | FAIL | FAIL | LOW | MED |
| src/operational_model/matrices/si_matrix.py | 47 | OK | OK | OK | OK | OK | OK | FAIL | FAIL | LOW | MED |
| src/operational_model/matrices/vi_matrix.py | 69 | OK | OK | OK | OK | OK | OK | FAIL | FAIL | LOW | MED |
| src/operational_model/routing/__init__.py | 8 | OK | OK | OK | OK | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/routing/context.py | 52 | OK | OK | OK | OK | OK | OK | OK | FAIL | LOW | LOW |
| src/operational_model/routing/context_route.py | 19 | OK | OK | OK | OK | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/routing/routing_projection.py | 109 | OK | OK | OK | OK | FAIL | OK | FAIL | FAIL | LOW | MED |
| src/operational_model/routing/search_vector.py | 39 | OK | OK | OK | OK | OK | OK | OK | FAIL | LOW | LOW |
| src/operational_model/system/__init__.py | 28 | OK | OK | OK | FAIL | OK | OK | OK | OK | LOW | LOW |
| src/operational_model/system/logical_system.py | 109 | OK | OK | OK | FAIL | FAIL | OK | FAIL | FAIL | LOW | MED |
| src/operational_model/system/logical_system_queries.py | 70 | OK | OK | OK | FAIL | OK | OK | OK | FAIL | LOW | MED |
| src/operational_model/system/logical_system_registry.py | 96 | OK | OK | OK | FAIL | FAIL | OK | OK | FAIL | LOW | MED |
| src/operational_model/system/wi_game_queries.py | 56 | OK | OK | OK | FAIL | OK | OK | OK | FAIL | LOW | MED |
| src/operational_model/system/wi_game_registry.py | 95 | OK | OK | OK | FAIL | FAIL | OK | OK | FAIL | LOW | MED |
| src/operational_model/system/wi_game_serialization.py | 129 | OK | OK | OK | FAIL | FAIL | OK | OK | FAIL | LOW | MED |
| src/operational_model/system/wigame.py | 119 | OK | OK | OK | FAIL | FAIL | OK | FAIL | FAIL | LOW | MED |
| src/subcontext_routing.py | 342 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | HIGH | HIGH |
| src/tkm_orchestrator.py | 80 | FAIL | OK | FAIL | FAIL | OK | OK | FAIL | FAIL | LOW | HIGH |
| src/unified_engine.py | 578 | OK | OK | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | HIGH | HIGH |
| src/unified_engine_core/__init__.py | 8 | OK | OK | OK | OK | OK | OK | OK | OK | HIGH | LOW |
| src/unified_engine_core/bridge.py | 17 | OK | OK | OK | OK | OK | OK | OK | OK | HIGH | LOW |
| src/unified_engine_core/context.py | 17 | OK | OK | OK | OK | OK | OK | OK | OK | HIGH | LOW |
| src/unified_engine_core/symbol_registry.py | 39 | OK | OK | OK | OK | OK | OK | FAIL | OK | HIGH | LOW |
| src/unified_engine_core/truth_value.py | 30 | OK | OK | OK | OK | OK | OK | OK | FAIL | HIGH | LOW |

## Test Files

| File | Lines | MDoc | CDoc | FDoc | Dir<=5 | File<=80 | 1Class/File | <=2Meth/Class | <=8LineFn | DupRisk | Quality |
|---|---|---|---|---|---|---|---|---|---|---|---|
| tests/__init__.py | 0 | FAIL | OK | OK | FAIL | OK | OK | OK | OK | LOW | MED |
| tests/test_dimensional_collapse.py | 56 | FAIL | OK | FAIL | FAIL | OK | OK | OK | FAIL | MED | MED |
| tests/test_matrix_engine.py | 70 | FAIL | OK | FAIL | FAIL | OK | OK | OK | FAIL | HIGH | MED |
| tests/test_operational_model.py | 162 | FAIL | OK | FAIL | FAIL | FAIL | OK | OK | FAIL | MED | HIGH |
| tests/test_tkm_atom_map.py | 107 | FAIL | OK | FAIL | FAIL | FAIL | OK | OK | FAIL | MED | HIGH |
| tests/test_tkm_implementation.py | 115 | FAIL | OK | OK | FAIL | FAIL | OK | OK | FAIL | MED | MED |
| tests/test_tkm_orchestration.py | 77 | FAIL | OK | FAIL | FAIL | OK | OK | OK | FAIL | MED | MED |
| tests/test_tkm_roundtrip_suite.py | 99 | FAIL | OK | OK | FAIL | FAIL | OK | OK | FAIL | MED | MED |
| tests/test_unified.py | 127 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | MED | HIGH |
| tests/test_whitepaper_ingestion.py | 103 | FAIL | OK | FAIL | FAIL | FAIL | OK | OK | FAIL | MED | HIGH |
| tests/test_wikipedia_solar_system.py | 154 | FAIL | OK | OK | FAIL | FAIL | OK | OK | FAIL | MED | MED |

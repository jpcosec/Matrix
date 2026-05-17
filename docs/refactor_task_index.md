# Refactor Task Index

This index organizes the refactor around the repository rules captured in `docs/coding_standards.md` and the file-by-file audit in `docs/refactor_rules_matrix.md`.

## Priorities

### P0 - Make the new standard visible and enforceable

- Add missing module, class, and function docstrings across all audited Python files.
- Keep the audit matrix current after each major refactor pass.
- Add a lightweight validation script later so docstring and file-structure regressions are caught early.

### P1 - Complete the operational model package split

- `src/operational_model/` is now grouped into subpackages, but the split still needs cleanup and simplification.
- Current subpackages:
  - `src/operational_model/core/`
  - `src/operational_model/matrices/`
  - `src/operational_model/routing/`
  - `src/operational_model/system/`
- Remaining work:
  - add any missing docstrings and trim long files
  - reduce high-method classes in `system/`
  - keep package boundaries stable as legacy engines migrate onto them

### P2 - Split oversized and over-responsible classes

- `src/operational_model/system/wigame.py` is currently the most overloaded part of the new model.
- Split it into focused collaborators such as:
  - `WiGame`
  - `WiGameSerializer`
  - `WiGameSearchService`
  - `WiGameFactRegistry`
- `src/operational_model/system/logical_system.py` should likely become a smaller orchestration layer plus registration/search services.

### P3 - Tame the legacy engines

- Highest-risk legacy files:
  - `src/unified_engine.py`
  - `src/boolean_matrix_engine.py`
  - `src/context_composition.py`
  - `src/subcontext_routing.py`
  - `src/multivalued_engine.py`
  - `src/matrix_engine.py`
- These files violate several structure rules simultaneously: missing docstrings, many classes per file, long functions, and high duplication risk.
- Refactor direction:
  - move shared matrix helpers into reusable units
  - migrate proposition/fact logic onto `src/operational_model/`
  - split each engine into domain model, matrix ops, query service, serialization, and demos/examples

### P4 - Repair the tests as first-class modules

- Most tests are also missing module and function docstrings.
- Some test files are oversized and currently encode too many scenarios in one file.
- Split tests by behavior instead of by historical module when practical.
- Repair the known broken tests in the older stack after the engine split.

### P5 - Publish the class diagram

- Draw the operational model as boxes before the next structural pass.
- Minimum expected nodes:
  - `Thing`
  - `Relation`
  - `Proposition`
  - `Fact`
  - `LiSpace`
  - `WiGame`
  - `ViMatrix`
  - `SiMatrix`
  - `SearchVector`
  - `RoutingProjection`
  - `Context`
  - `LogicalSystem`
- Use the diagram to verify that coupling only flows where intended.

### P6 - Redesign `Si` semantic states after the structural split settles

- Replace the current flat `SenseValue` enum with explicit German-named dataclass states.
- Target hierarchy:
  - `SinnvollTatsache`
  - `SinnvollUnabgebildet`
  - `SinnlosTautologisch`
  - `SinnlosWiderspruechlich`
  - `UnsinnigFehlgebildet`
  - `UnsinnigAusserhalb`
- `__str__` for those classes should print the explanation in English.
- `SinnvollUnabgebildet` should cover the current "not mapped" case.
- `UnsinnigAusserhalb` should be treated as a subtype of `unsinnig`.

## Execution Order

1. Stabilize docs and audit artifacts.
2. Finish simplifying `src/operational_model/` after the subpackage split.
3. Split `WiGame` and `LogicalSystem` into smaller units.
4. Extract shared matrix/query/projection utilities.
5. Refactor the legacy engines onto the new package structure.
6. Rebuild the broken tests around the refactored APIs.
7. Add the class diagram and keep it synced with the code.

## File Clusters To Tackle First

### Cluster A - New operational core

- `src/operational_model/system/wigame.py`
- `src/operational_model/system/logical_system.py`
- `src/operational_model/matrices/boolean_matrix.py`
- `src/operational_model/matrices/vi_matrix.py`
- `src/operational_model/matrices/si_matrix.py`

Goal: reduce responsibility density before more features are added.

### Cluster B - Legacy monoliths

- `src/unified_engine.py`
- `src/boolean_matrix_engine.py`
- `src/context_composition.py`
- `src/subcontext_routing.py`
- `src/multivalued_engine.py`

Goal: break duplicated logic into reusable services and align them to the proposition-first model.

### Cluster C - Tests and examples

- `tests/test_operational_model.py`
- `tests/test_unified.py`
- `tests/test_dimensional_collapse.py`
- `tests/test_matrix_engine.py`

Goal: make the test surface match the new package boundaries and restore confidence in the suite.

# task-standards-01 - reduce oversized files and classes

## Goal

20 source files exceed the 80-line limit from `docs/coding_standards.md`. 9 classes exceed the 2-method limit. 3 files contain multiple classes. The codebase does not follow its own stated conventions.

## Objective

Reduce the worst violators below the coding standard thresholds without changing behavior.

## Non-Goals

- changing all 20 files at once (scope-limited to the worst 5)
- changing public APIs
- renaming or restructuring beyond what splitting requires

## Documentation References

- `docs/coding_standards.md`

## References

- `src/operational_model/system/s_expression_runtime.py` (393 lines, 21 methods)
- `src/operational_model/system/wigame.py` (129 lines, 17 methods)
- `src/operational_model/system/logical_system.py` (122 lines, 13 methods)
- `src/operational_model/routing/routing_projection.py` (121 lines, 9 methods)
- `src/operational_model/kernel/formulas.py` (145 lines, 8 classes)

## Exact Files To Change

- The 5 worst violators listed above

## Files To Avoid Unless Necessary

- test files
- `__init__.py` files

## Delete / Migrate Decision

- Oversized files — migrate (split into smaller units)

## End State

The 5 worst violators are brought under or near the coding standard thresholds.

## Exit Criteria

- No file in `src/` exceeds 130 lines (allow some tolerance for mature modules)
- No class exceeds 2 methods (excluding init and simple properties)
- All tests pass

## Suggested Implementation Path

1. Split `formulas.py` (8 formula classes → one class per file)
2. Split `WiGame` (17 methods → 3-4 focused classes)
3. Split `LogicalSystem` (13 methods → 2-3 focused classes)
4. Split `RoutingProjection` (9 methods → 2 classes)
5. `SExpressionRuntime` is tracked separately in task-refactor-01

## Validation

- `pytest -q`

## Failure Modes

- splitting creates circular imports
- splitting changes external behavior
- modules become too granular (diminishing returns)

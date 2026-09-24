# task-refactor-01 - split SExpressionRuntime god object

## Goal

`SExpressionRuntime` (393 lines, 21 methods) violates the coding standard (max 80 lines, max 2 methods per class) and centralizes too many responsibilities (parsing, symbol creation, relation creation, li-space creation, wigame creation, proposition check/assert/ingest, fact return, selector resolution, system management).

## Objective

`SExpressionRuntime` is split into focused collaborators without changing the public API surface or breaking the s-expression runtime interface.

## Non-Goals

- changing the s-expression syntax or wire format
- changing the class name or external interface
- performance optimization

## Documentation References

- `docs/architecture.md` — responsibility split
- `docs/coding_standards.md` — file/class/function size limits
- `docs/operations.md` — ingestion and evaluation flows

## References

- `src/operational_model/system/s_expression_runtime.py`

## Exact Files To Change

- `src/operational_model/system/s_expression_runtime.py`
- possibly new modules under `src/operational_model/system/`

## Files To Avoid Unless Necessary

- Any file outside `src/operational_model/system/`

## Delete / Migrate Decision

- `s_expression_runtime.py` — migrate (split, do not delete the public class)

## End State

Each sub-responsibility lives in its own file/class. `SExpressionRuntime` delegates to collaborators. No file exceeds 80 lines. No class exceeds 2 methods (excluding init).

## Exit Criteria

- All 114 tests still pass
- No file in `src/operational_model/system/` exceeds 80 lines
- SExpressionRuntime has at most 2 methods (orchestration only)
- The public API (`from src.operational_model import SExpressionRuntime`) still works

## Suggested Implementation Path

1. Identify the 5-6 responsibility clusters in the current class
2. Extract each cluster into its own module
3. Wire them back through SExpressionRuntime as delegates
4. Run test suite

## Validation

- `pytest -q`

## Failure Modes

- splitting creates inter-module circular imports
- splitting changes external behavior by accident
- over-splitting creates too many tiny files (diminishing returns)

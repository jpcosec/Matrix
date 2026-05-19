# Task: task-proto-shrdlu-02-lowering-and-dialog

## Goal

Turn the separate SHRDLU prototype into a real client of the Matrix kernel instead of a standalone parser demo.

## Objective

Lower prototype semantic frames into canonical runtime operations, add explicit ambiguity handling for dialogue references such as `it` and `them`, and provide a tiny execution harness only to prove the end-to-end idea.

## Non-Goals

- historical SHRDLU parity
- large blocks-world implementation
- web UI or renderer work

## Documentation References

- `docs/canonical_forms_and_ingestion.md`
- `docs/kernel_symbol_policy.md`
- `prototypes/shrdlu/README.md`

## References

- `DESK/tasks/task-runtime-02-s-expression-authoring-surface.md`
- `prototypes/shrdlu/`

## Exact Files To Change

- `prototypes/shrdlu/english_parser.py`
- `prototypes/shrdlu/lowering.py`
- `prototypes/shrdlu/dialog_state.py`
- `prototypes/shrdlu/proto.py`
- `tests/test_shrdlu_lowering.py`
- `tests/test_shrdlu_dialog.py`

## Files To Avoid Unless Necessary

- stable core docs
- unrelated runtime internals

## Delete / Migrate Decision

- parser-only prototype status: migrate into a kernel client prototype
- heavy blocks-world dependence: defer; keep world harness minimal and only for proof

## End State

The SHRDLU prototype can parse, lower, ask for disambiguation when needed, and execute against a tiny proof harness.

## Exit Criteria

- frame lowering exists
- unresolved-reference handling exists for simple dialogue cases
- tiny harness proves at least one command and one query end to end

## Suggested Implementation Path

1. Define frame-to-runtime lowering.
2. Add dialogue state for unresolved references.
3. Add a tiny execution harness.
4. Add tests.

## Validation

- `pytest tests/test_shrdlu_lowering.py tests/test_shrdlu_dialog.py`

## Failure Modes

- growing the prototype world into architecture instead of keeping it a proof harness

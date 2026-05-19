# Task: task-bool-03-bitwise-matrix-execution

## Goal

Translate the propositional and Boolean kernel into matrix-friendly execution primitives suitable for SixVi.

## Objective

Define and implement the first bitwise or matrix-oriented execution layer for kernel formulas, including connective evaluation over vectors/masks, propagation of constants, and reduction-oriented passes.

## Non-Goals

- complete GPU backend
- full DB symbol grounding
- prototype dialogue features

## Documentation References

- `DESK/tasks/task-prop-02-evaluator-and-classification.md`
- `DESK/tasks/task-bool-01-boolean-algebra-kernel.md`
- `DESK/tasks/task-bool-02-truth-tables-and-bit-basis.md`

## References

- `src/operational_model/matrices/`
- `src/operational_model/kernel/`

## Exact Files To Change

- `src/operational_model/kernel/bitwise_execution.py`
- `src/operational_model/kernel/boolean_functions.py`
- `src/operational_model/kernel/__init__.py`
- `tests/test_bitwise_execution.py`

## Files To Avoid Unless Necessary

- prototype packages
- unrelated routing code

## Delete / Migrate Decision

- scalar-only connective evaluation: migrate toward vector or mask-friendly execution
- hidden constant propagation in ad hoc simplifiers: migrate into explicit bitwise passes

## End State

Kernel formulas can be evaluated and reduced through explicit bitwise or matrix-friendly execution primitives aligned with SixVi.

## Exit Criteria

- core connectives work over vectorized truth assignments or masks
- constants `0/1` propagate correctly
- reduction passes remove duplicates, dominated structures, or trivial clauses where applicable
- tests prove equivalence with scalar truth-table evaluation

## Suggested Implementation Path

1. Define a small vector or mask execution abstraction.
2. Map named Boolean functions onto it.
3. Add constant propagation and reduction passes.
4. Test vectorized results against scalar evaluation.

## Validation

- `pytest tests/test_bitwise_execution.py`

## Failure Modes

- baking backend-specific assumptions into the public kernel API too early
- letting bit order or mask conventions remain implicit

# Task: task-bool-02-truth-tables-and-bit-basis

## Goal

Give the kernel an explicit basis in truth tables and bit patterns so every binary connective and every directly derivable inference over two variables can be represented operationally.

## Objective

Model the 16 binary Boolean functions, their truth-table rows, their bit encodings, their natural names or aliases where relevant, and the derived immediate inference patterns they support.

## Non-Goals

- full matrix backend implementation
- full normal-form simplifier
- Wi atom grounding

## Documentation References

- `docs/kernel_symbol_policy.md`
- `DESK/tasks/task-prop-02-evaluator-and-classification.md`
- `DESK/tasks/task-bool-01-boolean-algebra-kernel.md`

## References

- truth-table material gathered from Wikipedia category work on propositional logic and Boolean algebra
- the 16 binary Boolean functions (`f1`..`f16`) and their common named connectives

## Exact Files To Change

- `src/operational_model/kernel/boolean_functions.py`
- `src/operational_model/kernel/__init__.py`
- `tests/test_boolean_functions.py`
- `docs/kernel_symbol_policy.md`

## Files To Avoid Unless Necessary

- prototype packages
- Wi runtime mutation code

## Delete / Migrate Decision

- implicit connective semantics spread across handlers: migrate into explicit truth-table objects
- undocumented bit encodings: migrate into stable code and tests

## End State

The kernel has a first-class representation of binary Boolean functions with names, truth tables, and bit encodings.

## Exit Criteria

- 16 binary functions are represented explicitly
- named functions such as `and`, `or`, `if`, `iff`, `nand`, `nor`, `xor` are mapped clearly
- bit encoding is test-covered
- direct table-driven evaluation is possible from the representation

## Suggested Implementation Path

1. Define a dataclass for binary Boolean functions.
2. Encode the 16 functions with row order and bit pattern policy.
3. Add name and alias lookup.
4. Add tests for core connectives and a few uncommon ones.

## Validation

- `pytest tests/test_boolean_functions.py`

## Failure Modes

- choosing an undocumented row order for bit encodings
- mixing algebraic equivalence and named connective identity without explicit aliases

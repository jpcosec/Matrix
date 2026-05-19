# Task: task-prop-02-evaluator-and-classification

## Goal

Give the kernel a truth-functional semantics over SixVi-style truth assignments.

## Objective

Implement evaluation of propositional formulas as truth functions over atomic valuations and classify formulas as tautological, contradictory, or contingent.

## Non-Goals

- rewrite optimization
- inference search
- atom-to-Wi resolution

## Documentation References

- `docs/kernel_symbol_policy.md`
- `docs/proposition_first_architecture.md`

## References

- `DESK/tasks/task-prop-01-grammar-and-precedence.md`
- `src/operational_model/core/truth_value.py`

## Exact Files To Change

- `src/operational_model/kernel/formula_evaluation.py`
- `src/operational_model/kernel/formulas.py`
- `src/operational_model/kernel/__init__.py`
- `tests/test_propositional_evaluator.py`

## Files To Avoid Unless Necessary

- Wi mutation code
- prototype packages

## Delete / Migrate Decision

- ad hoc connective handlers: delete by replacement with truth-function semantics

## End State

The kernel can evaluate formulas from atom valuations and classify their global valuation behavior.

## Exit Criteria

- `not`, `and`, `or`, and `if` have explicit truth tables
- formula classification is test-covered
- output is stable enough to feed SixVi diagnostics

## Suggested Implementation Path

1. Define valuation input shape.
2. Implement truth-function evaluator.
3. Enumerate valuations over referenced atoms.
4. Add tautology/contradiction/contingency classification.

## Validation

- `pytest tests/test_propositional_evaluator.py`

## Failure Modes

- conflating `unknown` Wi truth with pure propositional valuation semantics without an explicit policy

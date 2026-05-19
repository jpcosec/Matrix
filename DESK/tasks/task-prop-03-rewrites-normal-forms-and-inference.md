# Task: task-prop-03-rewrites-normal-forms-and-inference

## Goal

Turn propositional formulas into stable reduction targets and add a first explicit inference layer.

## Objective

Implement rewrite laws, derive normal forms such as NNF/CNF/DNF, and add a first small propositional inference toolkit over the kernel formulas.

## Non-Goals

- database integration
- Wi atom grounding
- prototype dialogue work

## Documentation References

- `docs/kernel_symbol_policy.md`
- `docs/proposition_first_architecture.md`

## References

- `DESK/tasks/task-prop-01-grammar-and-precedence.md`
- `DESK/tasks/task-prop-02-evaluator-and-classification.md`

## Exact Files To Change

- `src/operational_model/kernel/formula_rewrites.py`
- `src/operational_model/kernel/formula_normal_forms.py`
- `src/operational_model/kernel/formula_inference.py`
- `src/operational_model/kernel/__init__.py`
- `tests/test_propositional_rewrites.py`
- `tests/test_propositional_normal_forms.py`
- `tests/test_propositional_inference.py`

## Files To Avoid Unless Necessary

- Wi execution code
- prototype packages

## Delete / Migrate Decision

- implicit law usage only in developer reasoning: migrate into explicit kernel code

## End State

The kernel can normalize formulas and perform a first limited set of formal inferences.

## Exit Criteria

- De Morgan, double negation, commutativity, associativity, distributivity, and idempotence rewrites exist
- NNF/CNF/DNF derivation is test-covered
- first inference rules are explicit and tested

## Suggested Implementation Path

1. Implement rewrite primitives.
2. Build normal-form derivation on top of rewrites.
3. Add a small inference rule library.

## Validation

- `pytest tests/test_propositional_rewrites.py tests/test_propositional_normal_forms.py tests/test_propositional_inference.py`

## Failure Modes

- mixing equivalence-preserving rewrites with inference rules without distinction

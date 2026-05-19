# Task: task-bool-01-boolean-algebra-kernel

## Goal

Add the Boolean-algebra layer that turns the propositional kernel into a system of useful transformations, reductions, and matrix-friendly simplifications for SixVi.

## Objective

Implement the first explicit Boolean-algebra engine over kernel formulas, covering simplification laws, subsumption-friendly ordering, duality, and dimensional-reduction-oriented canonicalization.

## Non-Goals

- full propositional inference catalogue
- Wi atom grounding
- prototype dialogue work
- database implementation

## Documentation References

- `docs/kernel_symbol_policy.md`
- `docs/proposition_first_architecture.md`

## References

- `DESK/tasks/task-prop-01-grammar-and-precedence.md`
- `DESK/tasks/task-prop-02-evaluator-and-classification.md`
- `DESK/tasks/task-prop-03-rewrites-normal-forms-and-inference.md`

## Exact Files To Change

- `src/operational_model/kernel/boolean_algebra.py`
- `src/operational_model/kernel/formula_rewrites.py`
- `src/operational_model/kernel/formula_normal_forms.py`
- `src/operational_model/kernel/__init__.py`
- `tests/test_boolean_algebra.py`
- `tests/test_boolean_subsumption.py`

## Files To Avoid Unless Necessary

- Wi runtime mutation code
- prototype packages
- relation semantics code outside shared formula interfaces

## Delete / Migrate Decision

- simplification only by hand-written case logic: migrate into explicit Boolean-algebra rules
- hidden dimensional-reduction assumptions: migrate into named reduction passes
- raw formula trees without canonicalization support: defer only where necessary

## End State

The propositional kernel has an explicit Boolean-algebra layer that can simplify, canonicalize, compare, and reduce formulas in ways that prepare them for SixVi-style matrix execution.

## Exit Criteria

- identity, dominación, idempotencia, absorción, De Morgan, and involución are implemented explicitly
- order/subsumption helpers exist for clause or formula comparison
- dual rules can be generated or represented systematically
- reduction behavior is test-covered

## Suggested Implementation Path

1. Implement base rewrite laws: identity, domination, idempotence, absorption, De Morgan, involution.
2. Add a canonical ordering for conjunction/disjunction children.
3. Implement subsumption/comparability helpers over literals and clauses.
4. Add duality-aware helper generation or mirrored rewrites.
5. Expose matrix-friendly reduction passes.

## Validation

- `pytest tests/test_boolean_algebra.py tests/test_boolean_subsumption.py`

## Failure Modes

- treating Boolean algebra as mere syntax sugar instead of the optimization layer for SixVi
- mixing truth-functional evaluation and algebraic equivalence without distinction
- allowing canonicalization to depend on incidental child order

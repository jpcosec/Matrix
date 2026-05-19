# Task: task-prop-01-grammar-and-precedence

## Goal

Define the first formal grammar of kernel-level propositional formulas so the s-expression core has a precise notion of well-formedness.

## Objective

Specify and implement the well-formed formula grammar for atomic propositions plus `and`, `or`, `not`, and `if`, together with explicit precedence and parenthesization policy.

## Non-Goals

- truth evaluation
- rewrite laws
- Wi execution bridge

## Documentation References

- `docs/canonical_forms_and_ingestion.md`
- `docs/kernel_symbol_policy.md`
- `docs/proposition_first_architecture.md`

## References

- `DESK/tasks/Board.md`
- `src/operational_model/language/s_expressions.py`

## Exact Files To Change

- `src/operational_model/kernel/formulas.py`
- `src/operational_model/kernel/__init__.py`
- `tests/test_propositional_grammar.py`
- `docs/kernel_symbol_policy.md`

## Files To Avoid Unless Necessary

- Wi runtime mutation/query modules
- prototype packages

## Delete / Migrate Decision

- ad hoc connective parsing: migrate into kernel formula parsing
- precedence-by-convention only: delete by replacing with explicit rules

## End State

The kernel can parse and validate well-formed propositional formulas built on the canonical s-expression surface.

## Exit Criteria

- explicit AST or dataclasses for formulas exist
- malformed formulas fail deterministically
- precedence rules are documented even if s-expressions remain fully parenthesized

## Suggested Implementation Path

1. Define formula dataclasses.
2. Reuse the s-expression parser as token structure input.
3. Validate legal operator arities.
4. Add tests for well-formed and malformed formulas.

## Validation

- `pytest tests/test_propositional_grammar.py`

## Failure Modes

- mixing Wi proposition parsing with kernel formula parsing
- leaving operator arity ambiguous

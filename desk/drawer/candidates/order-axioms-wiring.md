# Wire the order axioms into the places that could enforce them

ID: task-order-axioms-wiring
Status: deferred
Priority: medium

## Rationale

`RelationAlgebra` now declares `irreflexive`, `antisymmetric` and `total`, with
`is_strict_partial_order()`, `is_total_order()`, `requires_distinct_operands()` and
`validate_pairs()`. `core/relations/order.py` validates acyclicity and extracts the
sequence.

None of it is enforced automatically. A relation can be declared a total order and
then accumulate facts that violate antisymmetry, and nothing objects:
`validate_pairs()` has to be called by hand, and `WiGame.add_fact` does not consult
the algebra.

Same pattern as `information_energy` before this round: the capability exists and
no caller reads it.

## Goal

Enforce declared axioms at assertion time, with a typed rejection rather than a
silent accept.

## Scope

- `system/wigame.py` (`add_fact`) or `system/logical_system.py` (`add_fact`)
- `matrices/si_matrix.py` for the mechanical part of the diagonal

## Implementation path

Two pieces, separable:

1. **Cheap and mechanical.** `requires_distinct_operands()` is True for an
   irreflexive relation, so `(R a a)` is `unsinnig` by construction. Set the
   diagonal senseless when the Li space is built over matching axes. No
   fact-by-fact checking needed.
2. **Incremental validation.** On `add_fact`, if the relation declares
   antisymmetry, reject the mirror of an existing fact. Full `validate_pairs()` on
   every insert is O(n^2); the incremental check is O(1) per fact and catches the
   same violation.

Totality is different in kind: it is a property of a *complete* fact set, so it
cannot be checked incrementally. It belongs in a verification pass, not in
`add_fact`.

## Validation

- asserting `(precede a a)` on an irreflexive relation is rejected or marked unsinnig
- asserting both `(precede a b)` and `(precede b a)` on an antisymmetric relation
  is rejected, naming the axiom
- a relation with no declared axioms behaves exactly as today
- the existing 265 tests keep passing: default profiles declare nothing

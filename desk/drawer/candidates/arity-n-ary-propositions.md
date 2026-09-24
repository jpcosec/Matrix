# N-ary propositions: lift the arity-2 ceiling

ID: task-arity-n-ary-propositions
Status: deferred
Priority: medium

## Rationale

Arity is hardcoded to 2 in five places:

- `core/proposition.py` — exactly `subject_symbol_id` and `object_symbol_id`
- `Proposition.sexpr()` — `f"({relation_id} {subject} {object})"`
- `core/li_space.py` — exactly `axis_a` and `axis_b`; `accepts()` checks both
- `matrices/boolean_matrix.py` — `values[i][j]`, 2-D; Vi/Si/RoutingProjection inherit
- `RelationAlgebra.canonical_coordinate_pair` / `proposition_identity_key`

So `(dar alice libro bob)` is not representable. The workarounds all lose
something: dropping the third argument loses data; packing it into a composite
label is rejected by `accepts()` and, if forced onto the axis, makes the argument a
substring rather than a symbol (which is exactly what `shape_guard` now flags as
`packed_object`); reifying to an event node works but replaces one ternary
relation with three binaries plus an invented node.

## Goal

Decide whether to support arity > 2, and if so lift it in the model rather than in
the serializer.

## Scope

Model-level. `projection_emit` needs no change: it is faithful to the model, and
the model is binary. The dimensionality of `LiSpace` is the actual constraint.

## Notes

Lower priority than it looks. Now that `system/reflection.py` can reify relations
as symbols, the event-node workaround is principled rather than a hack: the event
gets a real symbol, its roles are ordinary binary relations, and the relation
itself can be predicated over. That covers most of what arity 3 was wanted for.

The honest question is whether native n-ary buys anything beyond what reification
already gives, given it would touch every matrix operation in the kernel.

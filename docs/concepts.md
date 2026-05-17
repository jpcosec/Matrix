# Concepts

Matrix combines a philosophical vocabulary about meaning with an operational model built from explicit propositions, local language games, and routing structures.

## Proposition-first stance

The project starts from propositions, not from object-property pairs.

- a proposition has the form `(R a b)`
- `R` is a relation
- `a` and `b` are things
- a fact is a proposition with a truth assignment

This keeps the logical form explicit and prevents object/property shortcuts from becoming the hidden architecture.

## Philosophical vocabulary

The project borrows from the *Tractatus Logico-Philosophicus* the idea that logical evaluation should happen over facts and their form, not only over isolated words.

- `sinnvoll`: a proposition is meaningful and can be evaluated truthfully inside the relevant game.
- `sinnlos`: a proposition is structurally empty in the relevant way, such as a tautological or contradictory case.
- `unsinnig`: a proposition is malformed or outside the relevant logical space, so evaluation is ill-formed.

These labels explain why a proposition succeeds or fails logical validation, not just whether it is true.

## Truth and sense

The active model keeps truth and sense separate:

- `Vi` stores factual truth values.
- `Si` stores semantic status.

This matters because a proposition can be false yet meaningful, or impossible to evaluate because it never forms a valid move in the current game.

## Local and routed spaces

- `WiGame` is the local language game where propositions and facts are evaluated.
- `Context` is the routing structure that can point to `WiGame` instances or other `Context` instances.
- `SearchVector (p_i)` expresses a local query inside one game.
- `RoutingProjection (r_i)` expresses how subjects project from one game into another.

This split keeps local semantics and cross-space navigation decoupled.

## Provenance

Observation is treated as fact-level provenance, not as a first-class matrix layer.

When provenance matters, it should live on `Fact` metadata through fields such as source, confidence, or derivation lineage.

## Semantic refinement

The sense vocabulary is expected to become more explicit over time. In particular, the current flat `Si` statuses may be replaced by finer-grained dataclass-level semantic states once the structural refactor settles.

## Code references

- `src/operational_model/core/`
- `src/operational_model/matrices/`
- `src/operational_model/routing/`
- `src/operational_model/system/`

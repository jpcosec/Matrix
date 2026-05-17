# Proposition-First Architecture

This document captures the stable architectural direction for Matrix after the shift away from the legacy unified-engine model.

## Core stance

Matrix is proposition-first, not object-property-first.

The primitive logical unit is a proposition of the form `(R a b)`, where:

- `R` is a relation
- `a` is the subject thing
- `b` is the object thing

The system should model `Thing`, `Relation`, `Proposition`, and `Fact` explicitly. A `Fact` is a proposition plus a truth assignment.

This avoids collapsing the logical structure into an `object -> property` shortcut and keeps the code aligned with the intended semantics.

## Canonical operational pieces

The active operational model is built around these concepts:

- `Thing`
- `Relation`
- `Proposition`
- `Fact`
- `LiSpace`
- `WiGame`
- `Context`
- `SearchVector (p_i)`
- `RoutingProjection (r_i)`

These concepts define the base architecture for new work. Legacy abstractions should not be reintroduced unless they are explicitly redesigned in terms of this model.

## `WiGame` and `Context`

`WiGame` and `Context` are not synonyms.

- `WiGame` is a local evaluative language game.
- `Context` is a routing structure that can point to another `Context` or to a `WiGame`.

The recursive rule is:

- `Context -> Context | WiGame`

Responsibilities are split cleanly:

- facts live in `WiGame`
- routing lives in `Context`

This separation keeps local truth evaluation distinct from hierarchical navigation.

## Facts, observation, and provenance

Observation should not survive as a first-class `Oi` matrix in the new architecture.

If observation or provenance is needed, it belongs on `Fact` metadata. Typical examples include:

- `observed`
- `source`
- `derived_from`
- `confidence`

This keeps provenance attached to the evaluable unit it qualifies instead of preserving an extra structural layer just because it existed in the legacy runtime.

## Sense-state direction

The old flat `Si` labels are too coarse for the intended semantics. The target direction is to represent sense states as explicit dataclass-level variants instead of enum-like buckets.

Target categories:

- `SinnvollTatsache`
- `SinnvollUnabgebildet`
- `SinnlosTautologisch`
- `SinnlosWiderspruechlich`
- `UnsinnigFehlgebildet`
- `UnsinnigAusserhalb`

This keeps semantic distinctions explicit and reduces drift in how `sinnvoll`, `sinnlos`, and `unsinnig` are used across code and tests.

## Design constraints

When extending the operational model:

- do not reintroduce `property` as a primitive in place of proposition structure
- do not put factual truth logic on `Context`
- do not treat `WiGame` as a generic container node
- do not rebuild `Oi` as a structural matrix by default
- do not keep the old `Si` vocabulary if the implementation needs finer distinctions

## Failure modes

Typical architectural regressions include:

- designing APIs around `(object, property)` instead of `(relation, subject, object)`
- mixing routing concerns with local fact evaluation
- recreating legacy matrix layers without a proposition-first justification
- using sense labels loosely instead of preserving the intended semantic split

# Architecture

Matrix is organized around a proposition-first operational model rooted in `src/operational_model/`.

For the stable architectural stance, start with `docs/proposition_first_architecture.md`. This document gives the structural view of how the active code is organized.

## High-level flow

```text
Names and symbols
        |
        v
Thing / Relation / Proposition / Fact
        |
        v
WiGame (local evaluation)
        |
        +--> Vi truth matrix
        +--> Si sense matrix
        +--> p_i local search vector
        v
Context graph
        |
        +--> ContextRoute edges
        +--> r_i routing projections
        v
Search, routing, reconstruction, and serialization
```

## Main architectural pieces

1. `core/`
   Defines the primitive entities used throughout the system.
   - Code reference: `src/operational_model/core/`

2. `matrices/`
   Defines shared matrix structures such as truth and sense matrices.
   - Code reference: `src/operational_model/matrices/`

3. `system/`
   Defines local language-game behavior and aggregate orchestration.
   - Code reference: `src/operational_model/system/`

4. `routing/`
   Defines cross-space navigation through `Context`, `ContextRoute`, `SearchVector`, and `RoutingProjection`.
   - Code reference: `src/operational_model/routing/`

## Responsibility split

- `Thing`, `Relation`, `Proposition`, and `Fact` define the logical substrate.
- `WiGame` is the local evaluative space where propositions can be queried and facts can be assessed.
- `Context` is the routing layer that organizes how one local space can lead to another.
- `SearchVector (p_i)` expresses what is being requested inside a `WiGame`.
- `RoutingProjection (r_i)` expresses how subjects in one game project into another.

## Evaluation model

The active model preserves a clean distinction between truth and sense:

- `Vi` stores factual truth values.
- `Si` stores whether a position is meaningful, tautological, contradictory, or malformed.

Observation and provenance do not require a dedicated legacy matrix layer. When needed, they belong on `Fact` metadata.

## Routing and reconstruction

Reconstruction moves from a fact-bearing local space toward the structures that can explain or restate it:

1. Identify the relevant fact or proposition.
2. Search locally within the relevant `WiGame`.
3. Route across `Context` boundaries when the answer depends on another space.
4. Project subjects through `r_i` when crossing games.
5. Reconstruct a language-facing representation from the linked facts and symbols.

## Legacy status

The old unified-engine stack is no longer the architectural source of truth. If historical files remain in the repository, they should be treated as migration surfaces rather than design references.

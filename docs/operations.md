# Operations

This document describes the main workflows of the active proposition-first model.

## 1. Ingestion

Ingestion should map external material toward explicit proposition structure.

The intended flow is:

1. resolve or create the relevant names and symbols
2. identify the relation and the two participating things
3. create a proposition in canonical form `(R a b)`
4. attach a truth assignment to produce a fact
5. place that fact in the appropriate `WiGame`

If the relevant local game or routing path does not exist yet, the system may need to extend its structural space before the fact can be grounded cleanly.

## 2. Local evaluation

Local evaluation happens inside a `WiGame`.

At that layer, the system combines:

- `Vi` for truth
- `Si` for semantic status

This allows the system to explain whether a proposition is meaningful, tautological, contradictory, malformed, or simply unevaluated.

## 3. Algebraic inference

When a fact is added to the system, the operational model applies algebraic properties declared in the `Relation` to infer additional facts.

- **Commutative**: If `(R a b)` is true, the system infers `(R b a)`.
- **Transitive**: If `(R a b)` and `(R b c)` are true, the system infers `(R a c)`.

These inferences happen automatically during fact registration in the `LogicalSystem` and are propagated into the relevant `WiGame` matrices.

## 4. Querying

Local search is expressed through `p_i` (`SearchVector`):

- `p_i` lives on the `ejeB` axis of a `WiGame`
- it marks which terms are being requested inside that game
- it is evaluated against `Vi`, while `Si` filters malformed or semantically invalid positions

Typical uses include:

- searching for subjects that satisfy a set of requested terms
- detecting dimensions that do not discriminate locally
- narrowing candidate facts before cross-context routing

## 4. Routing and projection

When knowledge spans multiple local games, routing proceeds through `Context` and `RoutingProjection`.

- `Context` determines where navigation can go next
- `r_i` determines how subjects in one game project into another

This supports workflows such as:

- search locally in one game
- project the matching subjects into a second game
- intersect the projected results with a second local query
- continue routing if a higher-level context requires another hop

## 5. Reconstruction

Reconstruction works by moving from fact-bearing structures back toward language-facing ones.

Typical sequence:

1. locate the relevant fact
2. recover the local proposition structure
3. route to any supporting spaces if the explanation depends on them
4. recover names, symbols, and relations
5. emit a reconstructable textual representation

The round-trip scenario in `tests/test_tkm_roundtrip_suite.py` remains the best executable reference for this workflow.

## 6. Export direction

Export should preserve the proposition-first structure instead of serializing through legacy matrix-specific assumptions.

Preferred external artifacts include:

- canonical proposition text
- `WiGame` serialization
- routing-aware structures that can be inspected or transformed by downstream tools

## Code references

- `src/operational_model/system/`
- `src/operational_model/routing/`
- `src/operational_model/matrices/`

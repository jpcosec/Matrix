# Operations

This document describes the main ways the TKM/MEEL stack is meant to be used in practice.

## 1. Ingestion and schema growth

`TKMOrchestrator` provides an LLM-oriented workflow for mapping natural language into the current logical space.

The intended decision flow is:

1. map directly to an existing subject/property
2. map semantically to an existing symbol
3. expand the schema with a new object, property, or context-facing element

Once the decision is made, the orchestrator updates the symbol registry, extends the context when needed, and writes the fact into the engine.

- Code reference: `src/tkm_orchestrator.py`

## 2. Status evaluation

`get_status` is the central logical query.

It combines:

- the factual layer (`V_i`)
- the applicability layer (`S_i`)
- the explicit truth value labels

The result explains whether a proposition is `sinnvoll`, `sinnlos`, or `unsinnig`, rather than only returning a raw boolean.

- Code reference: `src/unified_engine.py`

## 3. Querying and discrimination

The engine can filter objects by property conjunctions and identify dimensions that fail to distinguish between candidates.

In the proposition-first operational model, local search is expressed through `p_i` (`SearchVector`):

- `p_i` lives on the `ejeB` axis of a `WiGame`
- it marks the terms requested inside that game
- it is evaluated against `Vi`, while `Si` filters malformed positions

Typical uses:

- search for objects that satisfy a set of properties
- detect tautological dimensions
- detect ambiguous objects that remain under-specified

Code reference: `src/operational_model.py`

## 4. Bridge routing and composition

When knowledge is split across contexts, bridges provide the explicit routing structure.

In the new operational model, crossings are expressed through `r_i` (`RoutingProjection`):

- rows are subjects in the source `WiGame`
- columns are subjects in the target `WiGame`
- `True` marks a valid projection from one game into another

This supports compositions such as:

- `W_animales_es_propiedades x r_proyeccion_animales_caninos x W_caninos_es_propiedades`

Important operations include:

- composing information across linked contexts
- projecting source hits into a target game
- intersecting projected hits with a target-side `p_i`
- collapsing dimensions into square routed views
- recursively propagating connectivity through bridge paths

Code references: `src/operational_model.py`, `src/unified_engine.py`

## 5. Descriptive inversion

Reconstruction works by moving from fact-bearing structures back toward language-facing ones.

Typical sequence:

1. locate the relevant fact in a factual context
2. traverse the bridges or structural contexts that explain it
3. recover symbols, templates, and constraints
4. emit a reconstructable textual form

The round-trip scenario in `tests/test_tkm_roundtrip_suite.py` is the best executable reference for this workflow.

## 6. Visualization and export

`TKMVisualizer` supports exporting matrix and tree-oriented views that can be consumed by external tooling such as YAML or PlantUML-based pipelines.

- Code reference: `src/unified_engine.py`

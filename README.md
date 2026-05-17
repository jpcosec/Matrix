# Matrix Engine

Matrix stands for **Minimal Agglomerative Text Retrieval Index**.

It is a logic-oriented knowledge engine for projecting natural-language statements into structured contexts, evaluating whether they are meaningful inside those contexts, and operating on the resulting matrices.

The project centers on **sense/meaning matrices**: a separation between truth (`V_i`) and applicability (`S_i`) inside logical worlds (`W_i`). On top of that representation, the engine supports search, ambiguity detection, tautology detection, context composition, bridge routing, and text-to-logic ingestion workflows.

## What is in this repository

- `cli.py` exposes the basic single-context engine from the command line.
- `src/matrix_engine.py` contains the original dictionary-based implementation.
- `src/operational_model.py` contains the new proposition-first operational model with `WiGame`, `Context`, `Vi`, `Si`, `p_i`, and `r_i`.
- `src/unified_engine.py` contains the multi-context engine with bridges, routing, and TKM-oriented utilities.
- `src/tkm_orchestrator.py` and `src/nl_parser.py` cover ingestion and parsing helpers.
- `examples/` and `tests/` provide working schemas and executable reference scenarios.
- `docs/README.md` is the entry point for the focused architecture and concepts docs.

## Quick start

Install the package and run the basic CLI against the sample schema:

```bash
pip install -e .
python cli.py examples/vegetales.yaml --status zanahoria hoja.rugosa
python cli.py examples/vegetales.yaml --query tallo
python cli.py examples/vegetales.yaml --tautologies
python cli.py examples/vegetales.yaml --ambiguous
```

If you want to work with the unified JAX-based engine, install JAX separately in your environment before importing `src/unified_engine.py`.

## Core ideas

- `W_i`: a logical context with its own objects, properties, metadata, and facts.
- `V_i`: the truth matrix for a context.
- `S_i`: the sense/applicability mask for a context.
- `p_i`: a search vector inside a `WiGame`.
- `r_i`: a routing projection between `WiGame` spaces.
- `O_i`: the observed mask for explicitly grounded facts.
- `D_i`: the discriminative mask used to identify non-informative dimensions.
- `sinnvoll` / `sinnlos` / `unsinnig`: statuses used to distinguish meaningful propositions, tautological or contradictory structure, and non-applicable propositions.

## Layered view

The repository spans a few related layers:

1. Natural-language input and parsing.
2. Symbol grounding and registry management.
3. Context modeling with object and property metadata.
4. Matrix construction for truth, sense, observation, and discrimination.
5. Operations such as querying, validation, composition, and bridge routing.

## CLI reference

```text
python cli.py <schema.yaml> [options]

Options:
  --query <prop> ...      Search objects matching all properties
  --status <obj> <prop>   Get the logical status of a proposition
  --tautologies           List tautological properties
  --ambiguous             List ambiguous objects
```

## Schema and examples

- Sample schema: `examples/vegetales.yaml`
- Additional examples: `examples/unified.yaml`, `examples/vegetales_hierarchical.yaml`, `examples/multivalued.yaml`
- Schema definition: `schemas/schema.yaml`

## Running tests

```bash
pytest
```

Some tests exercise the unified engine and therefore require the optional JAX dependency to be installed.

## Documentation map

- `docs/README.md` - docs index
- `docs/architecture.md` - context layers, bridges, and routing
- `docs/concepts.md` - philosophical and mathematical foundations
- `docs/data_models.md` - primary data structures
- `docs/operations.md` - ingestion, status evaluation, and reconstruction flows

## License

Apache 2.0

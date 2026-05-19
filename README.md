# Matrix Engine

Matrix stands for **Minimal Agglomerative Text Retrieval Index**.

It is a logic-oriented knowledge engine for projecting natural-language statements into structured contexts, evaluating whether relational propositions are meaningful inside those contexts, and operating on the resulting matrices.

The project centers on **sense/meaning matrices**: a separation between truth (`V_i`) and applicability (`S_i`) inside logical worlds (`W_i`). On top of that representation, the engine supports search, ambiguity detection, tautology detection, context composition, bridge routing, and proposition-first ingestion workflows.

## What is in this repository

- `src/operational_model/` contains the active proposition-first runtime with `Thing`, `Relation`, `Proposition`, `Fact`, `WiGame`, `Context`, `RoutingProjection`, and the kernel modules.
- `src/operational_model/kernel/` contains the kernel-side formula, Boolean, bitwise, and typed-assertion layers.
- `prototypes/shrdlu/` contains a separate prototype client that lowers controlled English into kernel/runtime operations.
- `examples/` and `tests/` provide working schemas and executable reference scenarios.
- `docs/README.md` is the entry point for the focused architecture and concepts docs.

## Quick start

Install the package, run the tests, and try the separate SHRDLU prototype:

```bash
pip install -e .
pytest
python prototypes/shrdlu/proto.py --once "Put the red block on the blue cube."
```

## Core ideas

- `W_i`: a logical context with its own admissible terms, relations, metadata, and facts.
- `aRb` / `(R a b)`: the general relational form used by the active model.
- `V_i`: the truth matrix for a context-relative relation over `axis_a x axis_b`.
- `S_i`: the sense/applicability mask for the same relational space.
- `kern:{symbol}`: the kernel namespace for non-relational atoms used by propositional formulas.
- `SearchVector`: a local query vector inside a `WiGame`.
- `RoutingProjection`: a projection between `WiGame` spaces.
- fact provenance: observation, source, derivation, or confidence stored on `Fact` metadata.
- `D_i`: the discriminative mask used to identify non-informative dimensions.
- `sinnvoll` / `sinnlos` / `unsinnig`: statuses used to distinguish meaningful propositions, tautological or contradictory structure, and non-applicable propositions.

## Layered view

The repository spans a few related layers:

1. Natural-language input and parsing.
2. Symbol grounding and registry management.
3. Context modeling with admissible terms, relations, and fact metadata.
4. Matrix construction for truth, sense, and discrimination.
5. Operations such as querying, validation, composition, and bridge routing.

## Runtime surface

The active direct surface is s-expression-first.

Current examples include:

```text
(create symbol dog perro)
(create relation es es)
(create li li:animales es (axis-a dog) (axis-b mammal))
(create wigame wigame:animales li:animales)
(ingest wigame:animales (es dog mammal))
(assert wigame:animales (es dog mammal))
(check wigame:animales (es dog mammal))
```

## Schema and examples

- Sample runtime data still lives under `examples/`
- Prototype dialogue demo lives under `prototypes/shrdlu/`
- Schema definition remains at `schemas/schema.yaml`

## Running tests

```bash
pytest
```

Some tests exercise the unified engine and therefore require the optional JAX dependency to be installed.

## Documentation map

- `docs/README.md` - docs index
- `docs/proposition_first_architecture.md` - stable architectural direction
- `docs/canonical_forms_and_ingestion.md` - canonical proposition format and ingestion rules
- `docs/kernel_symbol_policy.md` - kernel-vs-Wi distinction, execution layers, and atom policy
- `docs/rebuild_and_migration_policy.md` - migration and task policy
- `docs/architecture.md` - package layout and responsibility split
- `docs/concepts.md` - philosophical and proposition-first foundations
- `docs/data_models.md` - primary data structures
- `docs/operations.md` - ingestion, evaluation, routing, and reconstruction flows
- `docs/storage_boundary.md` - YAML-first persistence boundary and Postgres compatibility path

## License

Apache 2.0

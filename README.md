# Matrix Engine

Matrix stands for **Minimal Aglomerative Text Retrieval IndeX*.

A logical architecture for projecting natural language into operable boolean spaces.

This project implements **Sense|Meaning Matrices** — a framework that separates truth (`V_i`) from applicability/sense (`S_i`) within logical contexts (`W_i`). It enables semantic search, ambiguity detection, tautology detection, context composition, and logical validation of propositions.

## Quick start

```bash
pip install -e .
python cli.py examples/vegetales.yaml --status zanahoria hoja.rugosa
python cli.py examples/vegetales.yaml --query tallo
python cli.py examples/vegetales.yaml --tautologies
python cli.py examples/vegetales.yaml --ambiguous
```

## Architecture

The engine operates across layers:

1. **Natural Language** → text/signs
2. **Semantic Parsing** → propositions, roles, entities
3. **Symbol Grounding** → sign → contextual symbol
4. **Ontological Layer** → OWL-like class/property restrictions
5. **Logical Context** → `W_i` with objects, properties, relations, rules
6. **Matrix Layer** → `V_i` (truth) and `S_i` (sense/applicability)
7. **Operational Layer** → search, inference, disambiguation, composition

## Core concepts

- **V_i** — boolean matrix of truth values per object/property within context `W_i`
- **S_i** — boolean matrix of applicability: whether a proposition is well-formed in `W_i`
- **sinnvoll** — applicable and true/false
- **sinnlos** — tautological or contradictory within the context
- **unsinnig** — not applicable (the question itself has no sense in this context)

## CLI

```
python cli.py <schema.yaml> [options]

Options:
  --query <prop> ...      Search objects matching all properties
  --status <obj> <prop>   Get logical status of a proposition
  --tautologies           List tautological properties
  --ambiguous             List ambiguous objects
```

## Schema format

See `examples/vegetales.yaml` for a working example and `schemas/schema.yaml` for the type definition.

## Components

| Module | Description |
|--------|-------------|
| `matrix_engine.py` | Core engine with dict-based matrices |
| `boolean_matrix_engine.py` | JAX-accelerated boolean matrix operations |
| `unified_engine.py` | Multi-context engine with bridges and routing |
| `nl_parser.py` | Natural language → proposition parser |
| `context_composition.py` | Context composition and routing |
| `subcontext_routing.py` | Hierarchical subcontext navigation |

## License

Apache 2.0

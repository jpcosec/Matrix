# Matrix Documentation

This directory documents the stable architecture and engineering rules of Matrix.

## Core documents

- [Canonical Forms and Ingestion](./canonical_forms_and_ingestion.md) - canonical proposition form and ingestion constraints
- [Rebuild and Migration Policy](./rebuild_and_migration_policy.md) - how active rebuild work should treat legacy code
- [Architecture](./architecture.md) - package layout and responsibility split of the active operational model
- [Coding Standards](./coding_standards.md) - structural heuristics for files, classes, functions, and documentation
- [Concepts](./concepts.md) - philosophical vocabulary and proposition-first terminology
- [WiGame, Context and Disambiguation](./context_and_wigame.md) - why a WiGame is context-bound and how contexts disambiguate
- [KB Fan-out Harness](./kb_fanout_harness.md) - proposal/review pipeline, context indexing, and stress measurements
- [Operatoria: cómo leer una receta](./operatoria_recetas.md) - authored domain operatoria: relations, algebra, operations, typed errors
- [Data Models](./data_models.md) - the primary structures exposed by the operational model
- [Kernel Symbol Policy](./kernel_symbol_policy.md) - first stable distinction between kernel symbols and Wi-level relations
- [Operations](./operations.md) - ingestion, local evaluation, routing, and reconstruction workflows
- [Language to Matrix Ingestion Pipeline](./language_to_matrix_pipeline.md) - end-to-end 5-stage transformation from natural language text to Boolean matrix coordinates
- [Pure Boolean Matrix Architecture](./pure_boolean_matrix_architecture.md) - specification for matrix-first inference and bitwise execution
- [SHRDLU Prototype Architecture](./shrdlu_prototype.md) - controlled English parser, semantic frames, and lowering to Matrix S-Expressions
- [Storage Boundary](./storage_boundary.md) - persistence invariants between the YAML prototype and future DB-backed symbol spaces

## Deferred material

The JAX / `CanonicalHypertensor` architecture is abandoned and its documents
were moved out of this tree to [`../desk/drawer/jax/docs/`](../desk/drawer/jax/docs)
(with the rest of the deferral in [`../desk/drawer/jax/README.md`](../desk/drawer/jax/README.md)).
That includes the former `proposition_first_architecture.md` and the
`specs/architecture_{component,deployment,sequence,state}.*` diagrams, all of
which described a global tensor store that was never built. State lives in each
`WiGame`.

## Related repository resources

- Source code: `src/`
- KB harness: `tools/kb/` (ver [`tools/kb/README.md`](../tools/kb/README.md))
- Examples and versioned KBs: [`examples/README.md`](../examples/README.md)
- Tests and demos: `tests/`
- Whitepaper materials: `Whitepaper`

## Suggested reading order

1. Start with [Canonical Forms and Ingestion](./canonical_forms_and_ingestion.md).
3. Read [Rebuild and Migration Policy](./rebuild_and_migration_policy.md).
4. Read [Architecture](./architecture.md) for the package-level view.
5. Use [Data Models](./data_models.md) when mapping concepts to code.
6. Finish with [Operations](./operations.md) for execution flows.

## Quick verification

Run the test suite from the repository root:

```bash
pytest
```

If you only want to exercise the separate SHRDLU prototype, run:

```bash
python desk/drawer/shrdlu/proto.py --once "Put the red block on the blue cube."
```

To exercise the KB harness end to end without an LLM:

```bash
bash examples/regenerate.sh
python -m tools.kb --kb /tmp/kb_examples_machine reachability
python -m tools.kb --kb /tmp/kb_examples_machine capabilities
```

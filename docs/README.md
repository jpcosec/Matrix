# Matrix Documentation

This directory documents the stable architecture and engineering rules of Matrix.

## Core documents

- [Proposition-First Architecture](./proposition_first_architecture.md) - stable direction for the new operational model
- [Canonical Forms and Ingestion](./canonical_forms_and_ingestion.md) - canonical proposition form and ingestion constraints
- [Rebuild and Migration Policy](./rebuild_and_migration_policy.md) - how active rebuild work should treat legacy code
- [Architecture](./architecture.md) - package layout and responsibility split of the active operational model
- [Coding Standards](./coding_standards.md) - structural heuristics for files, classes, functions, and documentation
- [Concepts](./concepts.md) - philosophical vocabulary and proposition-first terminology
- [Data Models](./data_models.md) - the primary structures exposed by the operational model
- [Operations](./operations.md) - ingestion, local evaluation, routing, and reconstruction workflows

## Related repository resources

- Source code: `src/`
- Examples: `examples/`
- Tests and demos: `tests/`
- Whitepaper materials: `Whitepaper`

## Suggested reading order

1. Start with [Proposition-First Architecture](./proposition_first_architecture.md).
2. Read [Canonical Forms and Ingestion](./canonical_forms_and_ingestion.md).
3. Read [Rebuild and Migration Policy](./rebuild_and_migration_policy.md).
4. Read [Architecture](./architecture.md) for the package-level view.
5. Use [Data Models](./data_models.md) when mapping concepts to code.
6. Finish with [Operations](./operations.md) for execution flows.

## Quick verification

Run the test suite from the repository root:

```bash
pytest
```

If you only want the round-trip scenario, run:

```bash
python tests/test_tkm_roundtrip_suite.py
```

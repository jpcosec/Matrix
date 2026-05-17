# Matrix Documentation

This directory documents the TKM/MEEL-oriented parts of the repository: the multi-context engine, its logical model, and the higher-level ingestion and reconstruction flows.

## Core documents

- [Architecture](./architecture.md) - context layers, bridge routing, and the role of each engine component
- [Coding Standards](./coding_standards.md) - structural heuristics for files, classes, functions, and documentation
- [Concepts](./concepts.md) - philosophical vocabulary and matrix-level concepts used throughout the project
- [Data Models](./data_models.md) - the primary structures exposed by the unified engine
- [Operations](./operations.md) - ingestion, status evaluation, routing, and reconstruction workflows
- [Refactor Rules Matrix](./refactor_rules_matrix.md) - file-by-file audit against the structural standard
- [Refactor Task Index](./refactor_task_index.md) - prioritized refactor plan and execution order

## Related repository resources

- Source code: `src/`
- Examples: `examples/`
- Tests and demos: `tests/`
- Whitepaper materials: `Whitepaper`

## Suggested reading order

1. Start with [Architecture](./architecture.md).
2. Read [Concepts](./concepts.md) for terminology.
3. Use [Data Models](./data_models.md) when mapping concepts to code.
4. Finish with [Operations](./operations.md) for execution flows.

## Quick verification

Run the test suite from the repository root:

```bash
pytest
```

If you only want the round-trip scenario, run:

```bash
python tests/test_tkm_roundtrip_suite.py
```

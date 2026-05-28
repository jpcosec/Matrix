# task-data-01 - standardize ∅ character usage in YAML

## Goal

The empty-set character `∅` (U+2205) is used inconsistently in example YAML files: sometimes as a bare YAML scalar (`truth: ∅`), sometimes inside quoted strings (`'010∅∅'`). This is fragile, hard to type, and may cause issues with non-UTF-8 tooling or databases.

## Objective

Define a consistent policy for void/unknown markers in YAML and apply it to all example files.

## Non-Goals

- changing the runtime representation of void/unknown values in Python
- adding a database backend

## Documentation References

- `docs/storage_boundary.md`
- `schemas/schema.yaml`

## References

- All files under `examples/` that contain `∅`

## Exact Files To Change

- `examples/vegetales.yaml`
- `examples/multivalued.yaml`
- `examples/unified_vegetales.yaml`
- `examples/unified_colores.yaml`
- `examples/vegetales_hierarchical.yaml`
- `schemas/schema.yaml` (document the chosen convention)

## Files To Avoid Unless Necessary

- source code under `src/`
- serialization/deserialization logic (scope-limited to data only)

## Delete / Migrate Decision

- ∅ in YAML data files — migrate (standardize the convention)

## End State

All example YAML files use a consistent marker for void/unknown. The schema documents the convention.

## Exit Criteria

- `grep -r "∅" examples/` shows consistent usage pattern
- `yaml.safe_load()` still works on all example files

## Suggested Implementation Path

1. Decide the convention: keep `∅` but always in quoted strings, or replace with `~`/`null`/`""`
2. Apply consistently across all example files
3. Document the convention in `schemas/schema.yaml`

## Validation

- `python3 -c "import yaml; [yaml.safe_load(open(f)) for f in ['examples/vegetales.yaml', 'examples/multivalued.yaml']]"`

## Failure Modes

- changing the marker breaks the Python deserialization code that expects `∅`
- convention drift between examples and schema

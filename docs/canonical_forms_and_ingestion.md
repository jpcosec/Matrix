# Canonical Forms and Ingestion

This document defines the stable external form for propositions and the constraints that future ingestion flows must respect.

## Canonical proposition form

The canonical external textual representation of a proposition is:

- `(R a b)`

The compact notation `aRb` is acceptable only as philosophical shorthand in explanatory prose. It is not the storage, transport, or test format.

## Internal vs external form

Internal code should keep proposition structure in separated fields, such as:

- `relation_id`
- `subject_symbol_id`
- `object_symbol_id`

External textual form should use s-expressions.

This separation keeps parsing, serialization, and logical operations explicit while preserving a single canonical textual representation.

## Why this matters

Using `(R a b)` as the canonical form makes the system:

- explicit
- parseable
- serializable
- extensible

It also prevents format drift between code, tests, examples, and documentation.

## Documentation and test rule

Documentation and tests should use the canonical form whenever they refer to concrete propositions.

Avoid:

- mixed proposition formats in the same workflow
- tests written against non-canonical text forms
- ingestion pipelines that silently normalize multiple external formats without declaring one canonical target

## Ingestion direction

Future ingestion work should target the proposition-first model directly instead of extending legacy orchestration shapes.

That means:

- parsing toward proposition structure, not object-property shortcuts
- producing stable identifiers and grounded symbols that fit the operational model
- emitting or preserving canonical s-expression forms at the system boundary

The ingestion interface can evolve, but the canonical external proposition form should stay stable.

## Failure modes

Common ingestion and serialization failures include:

- storing propositions in mixed text formats
- letting shorthand notation leak into persisted artifacts
- coupling ingestion too tightly to legacy orchestration assumptions

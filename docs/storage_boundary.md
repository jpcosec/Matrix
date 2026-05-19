# Storage Boundary

This document defines the persistence boundary for Matrix.

## Current stance

The prototype remains **YAML-first**.

That means:

- examples, local experiments, and direct `WiGame` inspection should remain easy to serialize as YAML
- no current kernel or runtime feature should require Postgres just to function

## Future stance

The design should remain compatible with **DB-backed symbol spaces**, especially Postgres-backed ones.

That compatibility matters for:

- canonical symbol identifiers
- `instance`-based type spaces
- `equivalent`-based alias normalization
- future query planning over large symbol domains

## Stable invariants

The following should remain backend-independent:

1. canonical proposition form: `(R a b)`
2. stable symbol identifiers
3. relation identifiers and algebra profiles
4. kernel atom namespace: `kern:{symbol}`
5. distinction between kernel semantics and Wi-level facts
6. result shapes of core runtime operations

## Backend-specific freedom

The following may differ between YAML and Postgres-backed implementations:

- physical storage layout
- indexing strategy
- query acceleration structures
- cache materializations
- transaction boundaries

## Symbol spaces

Future DB-backed storage should expose the same semantic operations currently modeled in the kernel:

- class membership via `instance`
- canonicalization via `equivalent`
- symbol-space normalization before Wi or kernel execution

In other words, the database should not be just a dumb sink for facts. It should be able to preserve the same symbol-space behavior that the current `SymbolSpace` abstraction already models in memory.

## Design consequence

When changing persistence surfaces:

- keep YAML as the easiest inspection/debug format for the prototype
- avoid baking YAML-only assumptions into kernel semantics
- avoid baking Postgres-only assumptions into public APIs

The storage layer may change later. The kernel and proposition-first runtime contracts should not.

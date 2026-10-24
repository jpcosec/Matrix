# Src Directory: Tractatus IR Core Implementation

This directory contains the entire Lisp implementation of the Tractatus IR system, organized into core modules, smoke tests, architectural linter, and temporary snapshot storage.

## Overview
`src/` is a flat structure holding all core Lisp modules of the Tractatus IR system, following strict separation of concerns enforced by `lint-structure.lisp`.

## Hash-Based Implementation
This system uses a content-addressable hash-based architecture for node identity and fact lookup:
- `calculate-merkle-hash` (tractatus-periphery.lisp:42) generates node IDs by hashing their canonical form using Lisp's `sxhash`
- `truth-of` (tractatus-core.lisp:54) performs O(1) fact lookup by querying the world's fact hash table using the Sachverhalt's Merkle hash
- All facts are indexed by the hash of their originating Sachverhalt, ensuring content-based identity

## Core Modules (tractatus-*.lisp)
Each module uses its own package (except `tractatus-periphery` which extends `tractatus-core`):

### 1. tractatus-core.lisp (Microkernel)
- Base ontology: `node` (content-addressable base), `begriff` (concept), `gegenstand` (object), `sachverhalt` (state-of-affairs), `tatsache` (fact), `welt` (world with hash-table indices for facts/taxonomy/names)
- Logical syntax: `logische-regel` (validation rules), `tiene-sentido-p` (sense checking)
- Truth engine: `truth-of` (O(1) fact lookup via Merkle hash), `assert-tatsache` (fact ingestion with syntax validation)
- Projection macro: `def-template` (compiles text patterns to functions that inject facts into worlds)

### 2. tractatus-periphery.lisp (Core Utilities)
- `sinsentido-error` condition for invalid sense violations
- Content hashing: `calculate-merkle-hash` (uses `sxhash` of canonical forms for node identity)
- Taxonomy helpers: `register-begriff`, `register-gegenstand`, `concept-isa-p`, `instance-of-p`
- Stubs for NLP bridge: `extract-variables`, `instantiate-sexp`

### 3. tractatus-worlds.lisp (World Lifecycle & Naming)
- Ingestion policy: `*allowed-ingestion-kinds*` (`:repo`, `:doc`, `:section`, `:hyp`, `:session`, `:branch`, `:lang`, `:lex`)
- World ID normalization: `normalize-welt-segment` (strips non-alphanumeric chars)
- ID constructors: `make-doc-welt-id`, `make-repo-welt-id`, `make-branch-welt-id`, `make-lang-welt-id`, etc.
- Ingestion guard: `assert-ingestion-target` (blocks direct writes to non-allowed world kinds)
- Factory functions: `make-doc-welt`, `make-repo-welt`, etc.

### 4. tractatus-ring.lisp (Assimilation Pipeline: SLDB → NLP → Core)
- Sign index: `resolve-name` (polysemy resolution for text strings to logical object IDs)
- Taxonomy children index: `index-jerarquia`
- SLDB processing: `process-sldb-document` (extracts text fields, calls NLP bridge placeholder, resolves names, asserts facts)
- NLP stub: `text-to-candidate-sexps` (returns mock traces for color-related text)

### 5. tractatus-axes.lisp (Contextual Bit-Axis Indexing)
- Per-world axis stores: `define-axis`, `axis-values`
- Concept-axis projections: `project-concept`, `concept-axis-value`
- Bitstring generation: `axis-bitstring` (1-hot encoded axis values)
- Context masks: `context-mask` (filters active/inactive axes)
- Signature matching: `concept-signature`, `contextual-signature`, `matching-concepts`
- Import/export: `export-axis-state`, `import-axis-state`

### 6. tractatus-semantics.lisp (Formal Semantic Model)
- Logical statuses: `*logical-statuses*` (`:sinnvoll`, `:sinnlos-tautology`, `:sinnlos-contradiction`, `:unsinnig`, etc.)
- Data structures: `signature` struct (bits, masks, context, type), `fact` class (subject/predicate/object/context), `relation` class
- Semantic operations: `semantic-xor` (implemented), `semantic-and`/`semantic-or` (placeholders), `validate-signature`, `project-to-signature`
- Exports all key symbols for external use

### 7. tractatus-discrimination.lisp (Contextual Discrimination System)
- Dimension management: `define-dimension` (categorical one-hot), `find-dimension`
- Context management: `define-context` (universe/task/discrimination tree), `find-context`
- Discrimination matrices: `build-matrix`, `transpose-index`, `detect-collisions`
- Tree processing: `flatten-tree-paths` → `bit-dictionary` for signature generation
- Signatures: `concept-signature`, `concept-valid-mask`
- Neighbor lookup: `neighbors` (similar/contrastive concepts per dimension)

### 8. tractatus-persistence.lisp (Core World Serialization)
- Exports: `export-facts`, `export-sign-index`, `export-taxonomy`, `export-world-summary`
- Snapshot save: `save-welt-snapshot` (writes `welt.sexp`, `facts.sexp`, `signs.sexp`, `taxonomy.sexp`, `axes.sexp`, `bundle.sexp` to a directory)
- Snapshot load: `load-welt-snapshot` (rebuilds world from files)

### 9. tractatus-discrimination-persistence.lisp (Discrimination State Serialization)
- Exports: `export-discrimination-state` (dimensions/contexts/projections)
- Saves/loads: `save-discrimination-state`, `load-discrimination-state` (writes `discrimination.sexp`)
- Validates world ID matches on import

## Other Contents
- **7 smoke-test files**: Validate each core module (e.g., `axes-smoke-test.lisp`, `ring-smoke-test.lisp`)
- **lint-structure.lisp**: Architectural linter enforcing separation of concerns:
  - Core must be pure (no I/O, HTTP, JSON, or back-references to ring/worlds/semantics)
  - Ring cannot manage core load order
  - Runs automatically on load
- **tmp-snapshots/**: Directory for temporary world snapshot files generated during testing/ingestion

## Key Design Rules
- All node identity and fact lookup uses content-addressable hashing via `calculate-merkle-hash`
- Core modules are side-effect free; all I/O and external data handling is delegated to `tractatus-ring` and persistence modules
- World ingestion is restricted to allowed kinds via `tractatus-worlds` policies

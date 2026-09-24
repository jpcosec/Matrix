---
id: pill-06-shrdlu-naming-map
entity: Shrdlu doc class name corrections
status: implemented
---

## Why

Documentation in `docs/` references class names that don't exist: `EnglishParser`,
`Lowering`. These are artifacts of an older API surface that was renamed during
refactoring. Subagents reading the docs get confused.

## What

The mapping from wrong doc names to correct source names.

## Where

- **Wrong names in docs**: `docs/operations.md`, `docs/philosophy.md`,
  `docs/implementation.md`
- **Correct names in source**: `src/matrix/`

## Map

| Wrong (docs) | Correct (source) | Module |
|-------------|------------------|--------|
| `EnglishParser` | `Reader` / `Parser` (two-phase) | `src/matrix/reader.py` + `src/matrix/parser.py` |
| `Lowering` | `SExpressionRuntime` | `src/matrix/sexpr_runtime.py` |
| `Atom` | `Atom` (still correct) | `src/matrix/atom.py` |
| `Scope` | `Scope` (still correct) | `src/matrix/scope.py` |

## How

### What `EnglishParser` was
An earlier design that parsed natural-English-like syntax directly. It was
split into `Reader` (tokenizer) + `Parser` (grammar). Docs that say
"EnglishParser" should say "Reader/Parser" or describe the two-phase
tokenize-then-parse pipeline.

### What `Lowering` was
An earlier name for the evaluator/compiler that "lowers" s-expressions into
runtime operations. The current name is `SExpressionRuntime`.

### Correction rule
When editing docs:
- `EnglishParser` → `Reader` (tokenization) or `Parser` (parse tree construction)
  depending on context. If both are meant, say `Reader/Parser`.
- `Lowering` → `SExpressionRuntime` or just `Runtime`.

## How Not

- Do NOT rename source classes to match the old doc names.
- Do NOT use "EnglishParser" or "Lowering" in new code or new docs.
- Do NOT add aliases (e.g., `Lowering = SExpressionRuntime`) — fix the docs
  to match reality.

## Why (depth)

The names `EnglishParser` and `Lowering` were conceptually clearer ("parses
English-like syntax", "lowers to runtime ops") but were replaced during a
refactor that prioritized implementation clarity over conceptual naming.
The docs were never updated to reflect the new names.

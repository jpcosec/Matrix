---
id: pill-01-package-layout
entity: package directory structure
status: implemented
---

## Why

New contributors and subagents need to know where each piece of the system lives
without reading every file. Prevents misplaced code and import confusion.

## What

The `src/matrix/` directory is a flat Python package. Each module owns one
concept. There are no subpackages.

## Where

`src/matrix/`

| Module | Responsibility | Lines |
|--------|---------------|-------|
| `__init__.py` | Public API exports | 2 |
| `api.py` | Top-level entry points: `apply`, `call`, `recover` | 86 |
| `atom.py` | `Atom` value type | 18 |
| `sexpr_runtime.py` | `SExpressionRuntime` — all special-form eval methods | 481 |
| `symbol.py` | `Symbol` type | 60 |
| `printer.py` | S-expression pretty-printer | 86 |
| `serial.py` | `to_dict` / `from_dict` serialization | 100 |
| `evaluator.py` | Expression evaluation dispatch | 174 |
| `state.py` | Global/interactive state manager | 139 |
| `parser.py` | S-expression text parser (string → nodes) | 85 |
| `reader.py` | Tokenizer / reader | 93 |
| `scope.py` | `Scope` (lexical environment) | 44 |

Supporting directories:

| Path | Purpose |
|------|---------|
| `prototypes/` | Experimental/aspirational code, excluded from wheel builds |
| `tests/` | Pytest suite |
| `docs/` | Documentation (some aspirational content mixed in) |
| `DESK/` | Development methodology and task tracking |
| `examples/` | Standalone usage examples |

## How

- One class per module (exception: `sexpr_runtime.py` has the god object).
- Imports are always `from matrix.<module> import <Name>`.
- `__init__.py` re-exports only the public surface used by `api.py`.
- No `__all__` is defined; consumers import from `api` or directly from modules.

## How Not

- Do NOT add subpackages — the flat layout is intentional.
- Do NOT add circular imports — modules import from `atom`, `symbol`, `scope`
  but never import each other in both directions.
- Do NOT put business logic in `__init__.py`.

## Why (depth)

The flat layout keeps coupling visible. If modules grow too big they get split
into new peer modules, not nested packages. Nesting was tried in an earlier
iteration and created import headaches.

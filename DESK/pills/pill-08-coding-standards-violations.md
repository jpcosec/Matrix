---
id: pill-08-coding-standards-violations
entity: coding standards violations to fix
status: to-implement
---

## Why

The codebase has structural issues that make it hard to maintain, test, and
extend. This pill catalogs every known violation so subagents can fix them
systematically without rediscovery.

## What

A catalog of violations grouped by category, with severity and location.

## Where

All modules in `src/matrix/`.

## How

### Oversized entities

| Entity | Lines | Limit | Problem |
|--------|-------|-------|---------|
| `src/matrix/sexpr_runtime.py` | 481 | 200 | God object; every `eval_*` method lives here |
| `src/matrix/evaluator.py` | 174 | 150 | Slightly over; tight coupling to runtime |
| `src/matrix/state.py` | 139 | 150 | OK but close |

### Oversized classes

| Class | Lines | Limit | Problem |
|-------|-------|-------|---------|
| `SExpressionRuntime` | ~460 | 200 | God object with 40+ eval methods |
| `Scope` | 44 | 200 | OK |

### Duplication

**Pattern: repeated `elif` dispatching** — `sexpr_runtime.py` has a single
method `eval` with 40+ `elif` branches. This is the core structural violation;
fixing it (task-refactor-01) eliminates most of the other issues.

**Pattern: manual list/tuple type-checking** — Several places check
`isinstance(expr, list)` or `isinstance(expr, tuple)` when a single dispatch
or pattern match would suffice.

### Naming inconsistencies

| Location | Issue |
|----------|-------|
| `sexpr_runtime.py` | `checkArity` uses camelCase |
| `evaluator.py` | Some variables use `snake_case`, some use `camelCase` |
| Various | Mixed `args` vs `params` vs `body` for same concept |

### Missing structural elements

- No `__all__` in any module
- No `if TYPE_CHECKING` guards (though no circular imports currently)
- `__init__.py` just has imports — no doc comment describing the package
- No `py.typed` marker file
- `prototypes/` has no `__init__.py` — it's not a package, just a directory
  of loose scripts

### Type annotation gaps

- `SExpressionRuntime.eval` has no return type annotation
- Most `eval_*` methods have no annotations
- `evaluator.py` `evaluate` function has partial annotations
- `serial.py` `to_dict`/`from_dict` have no annotations

### How to fix (priority order)

1. **Split SExpressionRuntime** (task-refactor-01) — fixes the god object,
   the elif chain, the camelCase, and the line count in one move.
2. **Add docstrings** (task-doc-02) — fixes the 52 undocumented functions.
3. **Reduce oversized files** (task-standards-01) — only needed if refactor
   doesn't fully resolve the line counts.
4. **Add linter** (task-infra-01) — catches new violations going forward.

## How Not

- Do NOT fix `__all__` until after the refactor — exports will change.
- Do NOT add `py.typed` until mypy is configured and passes cleanly.
- Do NOT reformat `camelCase` variables in the runtime until the refactor
  moves them to new modules — fix names at the destination, not the source.
- Do NOT add `if TYPE_CHECKING` — there are no circular imports to fix.

## Why (depth)

The violations are almost all downstream of the single architectural decision
to put every special form into one class. Fix that first (task-refactor-01)
and most other violations either disappear or become trivial to fix. The
remaining issues (docstrings, annotations, __all__) are cosmetic and can be
done in any order.

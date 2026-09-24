---
id: pill-02-sexpr-runtime-patterns
entity: SExpressionRuntime eval dispatch
status: to-implement
---

## Why

`SExpressionRuntime` (481 lines in `src/matrix/sexpr_runtime.py`) handles every
special form builtin as a method on one class. It's a god object that must be
split into smaller, focused modules.

## What

The runtime is an expression evaluator for a Scheme-like s-expression language.
Each special form has a method `eval_<form>(self, args, scope)`. The `eval`
method dispatches on the car of the expression to the correct handler.

## Where

- **Current location**: `src/matrix/sexpr_runtime.py`
- **Target**: split into `src/matrix/builtins/` package or flat peer modules.

## How

### Current dispatch pattern

```python
def eval(self, expr, scope):
    if not isinstance(expr, list):
        return expr
    op = expr[0]
    if op == 'define':
        return self.eval_define(expr[1:], scope)
    elif op == 'if':
        return self.eval_if(expr[1:], scope)
    # ... 40+ elif branches ...
```

### Refactor approach

Group by category. Each group becomes its own module:

| Category | Methods | Target Module |
|----------|---------|--------------|
| Definitions | `eval_define` | `builtins/definitions.py` |
| Control flow | `eval_if`, `eval_begin`, `eval_while`, `eval_for`, `eval_try` | `builtins/control.py` |
| Functions | `eval_lambda`, `eval_apply`, `eval_map`, `eval_filter`, `eval_reduce` | `builtins/functions.py` |
| Pairs/lists | `eval_cons`, `eval_car`, `eval_cdr`, `eval_list`, `eval_len`, `eval_range` | `builtins/lists.py` |
| Arithmetic | `eval_add`, `eval_sub`, `eval_mul`, `eval_div`, `eval_lt`, `eval_gt`, `eval_equal` | `builtins/arithmetic.py` |
| Logic | `eval_not`, `eval_and`, `eval_or`, `eval_is` | `builtins/logic.py` |
| I/O | `eval_print`, `eval_display`, `eval_newline`, `eval_read`, `eval_error` | `builtins/io.py` |
| Quote/eval | `eval_quote`, `eval_quasiquote`, `eval_unquote`, `eval_eval`, `eval_atom`, `eval_type`, `eval_str`, `eval_num` | `builtins/meta.py` |
| State | `eval_set`, `eval_sload`, `eval_ssave`, `eval_ssym` | `builtins/state.py` |
| Import | `eval_import` | `builtins/imports.py` |

### Naming conventions

- Module names: **plural nouns** (`definitions.py`, `control.py`, ...)
- Each module exports a **dispatch dict** `HANDLERS: dict[str, HandlerFn]`
  where `HandlerFn = Callable[[list, Scope], Any]`
- The main runtime composes them: `HANDLERS = {**defs, **ctrl, ...}`

### Shared patterns

- Every `eval_*` signature: `(self, args: list, scope: Scope) -> Any`
- Error handling: raise `RuntimeError(msg)` with a descriptive message
- Scope access: `scope.get(name)`, `scope.set(name, value)`, `scope.define(name, value)`
- No type annotations on args beyond `list` and `Scope` — the refactor can add them.

### Delegation pattern (target)

```python
# sexpr_runtime.py (after split)
from matrix.builtins.definitions import DEFINITIONS
from matrix.builtins.control import CONTROL
# ...

HANDLERS: dict[str, HandlerFn] = {}
for module in (DEFINITIONS, CONTROL, FUNCTIONS, LISTS, ARITHMETIC, LOGIC, IO, META, STATE, IMPORTS):
    HANDLERS.update(module)

class SExpressionRuntime:
    def eval(self, expr, scope):
        if not isinstance(expr, list):
            return expr
        op = expr[0]
        handler = HANDLERS.get(op)
        if handler is None:
            raise RuntimeError(f"Unknown special form: {op}")
        return handler(expr[1:], scope)
```

## How Not

- Do NOT use inheritance or mixins — prefer composition via dict merge.
- Do NOT make `eval_*` methods standalone functions that take `self` — use
  plain functions; the runtime becomes a thin facade.
- Do NOT change the public API (`SExpressionRuntime.__init__`, `eval` signature).
- Do NOT touch evaluator's integration point with the runtime.
- Do NOT add new imports from `sexpr_runtime` in other modules during the
  split — import from the new `builtins/` modules directly.

## Why (depth)

The god-object approach worked for prototyping but makes testing, extending,
and reasoning about individual forms painful. A `HandlerFn` + dict approach
lets each module be tested in isolation, lets new forms be added without
touching the runtime class, and makes the dispatch table inspectable.

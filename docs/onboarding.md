# Developer Onboarding Guide

## Setup

```bash
git clone <repo-url> && cd Matrix
python -m venv .venv && source .venv/bin/activate  # or: uv venv && uv activate
pip install -e .
python -c "from src.operational_model import SExpressionRuntime; print('ok')"
```

## Running tests

```bash
python -m pytest tests/ -v                          # full suite
python -m pytest tests/test_s_expression_runtime.py -v  # single file
python -m pytest tests/ -v -x --tb=short            # stop on first failure, short tracebacks
python -m pytest tests/ -v -k "test_create"         # run tests matching a keyword
```

## Project structure

- `src/operational_model/` — core packages: `core/` (Thing, Relation, Proposition, Fact, Symbol), `matrices/` (Vi, Si, BooleanMatrix), `system/` (WiGame, SExpressionRuntime, LogicalSystem), `routing/` (Context, SearchVector), `kernel/` (Boolean formula layer), `language/` (s-expression parser).
- `prototypes/shrdlu/` — standalone prototype that lowers controlled English to s-expression runtime calls.
- `tests/` — per-module test files mirroring the operational model surface.
- `docs/` — architecture, concepts, operations, and standards documents.

## Core concepts

- **Atom** — a bare string (symbol id) used as the leaf of an s-expression; never a list.
- **Symbol** — a registered Thing with a symbol id and a sign (name string).
- **Scope** — the set of admissible terms and relations within a `LiSpace`; defines the axes of a truth matrix.
- **SExpressionRuntime** — evaluates `(operator args...)` lists against a `LogicalSystem`; the top-level dispatch inspects `expr[0]` and calls the matching `_eval_*` method.
- **Expressions** — parsed s-expressions are nested Python lists of strings; `(check (es dog mammal))` becomes `["check", ["es", "dog", "mammal"]]`.

## Adding a new special form

To add a new top-level operation (e.g. `(delete ...)`):

1. Add a method `_eval_delete(self, args: list[SExpression]) -> OperationResult` in `src/operational_model/system/s_expression_runtime.py`.
2. Register it in the `evaluate()` dispatch by adding an `elif head == "delete": return self._eval_delete(expr[1:])` branch after line 54.
3. Add tests in `tests/test_s_expression_runtime.py` following the existing `def test_eval_*` pattern.

## Linting

```bash
ruff check src/                                     # style and lint (config in pyproject.toml)
mypy src/                                           # static type checking
```

Both commands should pass before submitting changes.

## Where to look next

Read [docs/README.md](README.md) for the suggested document reading order.

---
id: pill-04-test-conventions
entity: test suite conventions
status: implemented
---

## Why

Tests are the only automated verification. Consistent patterns make them
readable and maintainable.

## What

How the pytest suite is structured and what conventions it follows.

## Where

`tests/`

| File | What it tests |
|------|---------------|
| `tests/test_api.py` | Public API (`apply`, `call`, `recover`) |
| `tests/test_serialization.py` | `to_dict` / `from_dict` roundtrips |
| `tests/test_evaluator.py` | Expression evaluation |
| `tests/test_evaluator_advanced.py` | Advanced evaluation scenarios |
| `tests/test_printer.py` | Pretty-printing |
| `tests/test_parser.py` | Text → s-expression parsing |
| `tests/test_scope.py` | Scope operations |

## How

### Framework
- **pytest** (no unittest.TestCase).
- Run: `python -m pytest tests/` or `uv run pytest tests/`.

### Fixtures
Defined in each test file or in `conftest.py` if shared:

```python
@pytest.fixture
def runtime():
    return SExpressionRuntime()
```

### Test naming
- Files: `test_<module>.py`
- Functions: `test_<what>`
- Classes (rare): `Test<Thing>`

### Assertions
- Plain `assert` — no `self.assertEqual` or `pytest.assert_*` helpers.

### Structure pattern
```python
def test_short_description_of_behavior():
    runtime = SExpressionRuntime()
    scope = Scope()
    result = runtime.eval(["define", "x", "hello"], scope)
    assert result is None
    assert scope.get("x") == "hello"
```

### Parametrization used sparingly
```python
@pytest.mark.parametrize("expr,expected", [
    (["+", 1, 2], 3),
    (["*", 3, 4], 12),
])
def test_arithmetic(expr, expected):
    ...
```

### Coverage gaps (from diagnostic)
| Gap | Severity |
|-----|----------|
| `eval_for` untested | high |
| `eval_try` untested | high |
| `eval_map` untested | medium |
| `eval_filter` untested | medium |
| `eval_reduce` untested | medium |
| `eval_sload` / `eval_ssave` / `eval_ssym` untested | high |
| `eval_display` / `eval_newline` untested | low |
| `eval_cons` / `eval_car` / `eval_cdr` untested | high |
| `eval_str` / `eval_num` / `eval_type` untested | medium |
| Serialization roundtrip stress tests missing | high |
| Error-path tests missing across all forms | medium |

## How Not

- Do NOT use `pytest.raises` without a match string — always provide `match=`.
- Do NOT write tests that depend on execution order — each test must be
  independent.
- Do NOT use `unittest.mock` — the design avoids external dependencies;
  no mocks needed.
- Do NOT put integration tests in unit test files — use separate files
  or mark with `@pytest.mark.integration`.

## Why (depth)

Plain `assert` keeps tests readable and avoids framework lock-in. The lack
of mocks is intentional — the s-expression evaluator is self-contained.
Coverage gaps exist because the test suite grew alongside the prototype.
Filling them (task-test-01) is the first priority after the refactor.

---
id: pill-07-linter-config-goals
entity: linter and type-checker configuration
status: to-implement
---

## Why

The repo has no linter config (`.ruff.toml`, `.flake8`) and no type-checker
config (`pyproject.toml` `[tool.mypy]`). Code quality relies entirely on
author discipline. This pill defines the rules a linter/type-checker config
should enforce once task-infra-01 is done.

## What

The target linter is **ruff** (replaces flake8/isort/autoflake). The target
type-checker is **mypy** (standard for non-strict optional typing).

## Where

Config files to create:
- `pyproject.toml` — `[tool.ruff]` and `[tool.mypy]` sections
- (no separate `.ruff.toml` — keep everything in `pyproject.toml`)

## How

### Ruff rules to enable

| Category | Rules | Reason |
|----------|-------|--------|
| Pycodestyle | `E`, `W` | Basic formatting (line length, spacing) |
| Pyflakes | `F` | Unused imports, undefined names |
| isort | `I` | Import ordering |
| McCabe | `C90` | Cyclomatic complexity (`max-complexity = 10`) |
| pylint | `PL` | Additional quality checks (`literal-membership`, `super-without-brackets`) |
| pyupgrade | `UP` | Modern Python idioms |
| bugbear | `B` | Likely bugs |
| perforator | `PERF` | Performance anti-patterns |
| pandas-vet | `PD` | (if pandas is used) |

### Rules to explicitly NOT enable

- `D` (pydocstyle) — docstrings will be added per pill-03 but enforcing
  format via linter is premature until all docstrings exist.
- `ANN` (flake8-annotations) — type coverage isn't high enough yet.
- `T20` (flake8-print) — `eval_print` needs print.

### Ruff config template

```toml
[tool.ruff]
target-version = "py311"
line-length = 88
exclude = ["prototypes", "DESK"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "C90", "PL", "UP", "B", "PERF"]
ignore = []

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["PLR2004"]  # allow magic values in tests
```

### Mypy config template

```toml
[tool.mypy]
python_version = "3.11"
strict = false  # start lenient, tighten later
check_untyped_defs = true
disallow_untyped_defs = false
ignore_missing_imports = true
exclude = ["prototypes/"]
```

### Pre-commit or script?

No pre-commit hook (user preference against CI hooks). Run via:
```
ruff check .
mypy src/
```

## How Not

- Do NOT add `# noqa` without a specific rule code — `# noqa: F841`.
- Do NOT add `# type: ignore` without a comment explaining why.
- Do NOT enable strict mypy mode until types cover 80%+ of the public API.
- Do NOT add `mccabe` (the old tool) — use ruff's `C90` which implements it.
- Do NOT enable `pydocstyle` rules — docstrings are being added but enforcing
  via linter will cause noise until the work is complete.

## Why (depth)

Ruff was chosen over Flake8 because it's orders of magnitude faster, covers
more rule categories in one tool, and has a unified config. MyPy is standard.
Starting non-strict avoids a massive annotation PR — task-doc-02 and
task-infra-01 can be done independently. Complexity checks (C90) are included
from day one because `SExpressionRuntime` already exceeds any reasonable
complexity limit.

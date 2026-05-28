---
id: pill-03-docstring-standard
entity: docstring convention for undocumented functions
status: to-implement
---

## Why

52 functions/classes in the codebase have no docstrings. Adding them requires
a consistent format so the result reads like one author wrote it.

## What

The docstring convention to use for all public functions, methods, and classes.

## Where

Every module in `src/matrix/` — target for task-doc-02.

## How

### Format: plain Google style (no Sphinx/NumPy markup)

```python
def function_name(arg1: type, arg2: type) -> ReturnType:
    """Short one-line summary.

    Optional longer description — only when the one-liner isn't enough.
    It can span multiple lines but should stay brief.

    Args:
        arg1: What this argument is.
        arg2: What this argument is.

    Returns:
        What the return value represents.

    Raises:
        RuntimeError: When and why this is raised.
    """
```

### Rules

1. **Always start with a one-line summary** on the same line as `"""`.
2. The summary ends with a period.
3. **Args** section only for functions with 2+ parameters. Single-param
   functions can describe the arg inline in the summary.
4. **Returns** section required for non-None return types. Omit if `-> None`.
5. **Raises** section only if the function raises.
6. Indent continuation lines by 4 spaces inside the docstring.
7. Use backticks for parameter names in the Args section? No — just `arg_name:`.
   Use backticks for code references like `` `SExpressionRuntime` `` in the
   description text.
8. No type annotations in docstring — types go in the function signature.

### Priority order for task-doc-02

Start with modules that have the lowest docstring coverage:
1. `sexpr_runtime.py` — 35 undocumented methods
2. `evaluator.py` — 5 undocumented functions
3. `state.py` — 4 undocumented functions
4. `api.py` — 3 undocumented functions
5. `serial.py` — 2 undocumented functions
6. `parser.py` — 2 undocumented functions
7. `printer.py` — 1 undocumented function

### Tone

- Technical, terse, imperative mood ("Return the car of the pair" not "Returns the car of the pair").
- No marketing language, no "simply", "just", "easily".
- One blank line between sections.

## How Not

- Do NOT use Sphinx `:param:` or `:return:` directives.
- Do NOT use NumPy-style section headers (`Parameters\n----------`).
- Do NOT write docstrings for private helpers (single underscore prefix).
- Do NOT add type information that duplicates the signature.
- Do NOT write doctest examples — examples belong in `examples/` or the test suite.

## Why (depth)

Google style was chosen because it's readable in both source form and
rendered form, doesn't require a Sphinx plugin, and is the most widely
adopted convention in the Python ecosystem. Keeping it plain means no
build-time doc generation dependency.

# task-doc-02 - document undocumented functions

## Goal

52 functions (24% of all functions) lack docstrings, violating `docs/coding_standards.md` which requires every function to have a docstring.

## Objective

Add docstrings to all 52 undocumented functions.

## Non-Goals

- rewriting existing docstrings
- changing function signatures or behavior
- adding type annotations (already 100% covered)

## Documentation References

- `docs/coding_standards.md`

## References

- All files under `src/` with undocumented functions (listed in DIAGNOSTIC.md)

## Exact Files To Change

Files with the highest concentration of undocumented functions:
- `src/operational_model/system/s_expression_runtime.py` (12 missing)
- `src/operational_model/matrices/vi_matrix.py` (2 missing)
- `src/operational_model/matrices/si_matrix.py` (2 missing)
- `src/operational_model/kernel/symbol_spaces.py` (6 missing)
- `src/operational_model/kernel/formula_rewrites.py` (4 missing)
- `src/operational_model/kernel/bitwise_execution.py` (5+ missing)
- (and others)

## Files To Avoid Unless Necessary

- test files
- `__init__.py` files

## Delete / Migrate Decision

- N/A (docstrings added, no migration)

## End State

Every function in `src/` has a module docstring, class docstring, and function docstring.

## Exit Criteria

- Automated check shows 226/226 functions documented

## Suggested Implementation Path

1. Run the docstring audit script to get the current list
2. Add docstrings file by file, prioritizing the worst offenders first
3. Re-run audit to confirm 100%

## Validation

- `python3 -c "(docstring audit script from DIAGNOSTIC.md)"` shows 226/226

## Failure Modes

- docstrings become meaningless just to satisfy the counter
- accidentally changing behavior via docstring side effects (unlikely in Python)

# task-doc-01 - fix broken doc reference

## Goal

`docs/operations.md` references a test file that does not exist, which misleads readers and reduces trust in the documentation.

## Objective

The broken reference to `tests/test_tkm_roundtrip_suite.py` is corrected to point to the actual test file or removed.

## Non-Goals

- auditing all docs for broken references (scope-limited)
- restructuring operations.md

## Documentation References

- `docs/operations.md`
- `docs/canonical_forms_and_ingestion.md`

## References

- `docs/operations.md:92`
- `tests/test_serialization_roundtrip.py` (the actual roundtrip test file)

## Exact Files To Change

- `docs/operations.md` — line 92

## Files To Avoid Unless Necessary

- other doc files
- source code

## Delete / Migrate Decision

- `docs/operations.md` reference — migrate (fix the text)

## End State

`docs/operations.md` points to an existing test file or removes the dangling reference.

## Exit Criteria

- `grep -r "test_tkm_roundtrip_suite" docs/` returns empty

## Suggested Implementation Path

1. Replace `tests/test_tkm_roundtrip_suite.py` with `tests/test_serialization_roundtrip.py`
2. Verify the new path actually exists

## Validation

- `grep "test_tkm_roundtrip_suite" docs/` → no matches

## Failure Modes

- None (text-only change)

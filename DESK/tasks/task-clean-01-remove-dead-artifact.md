# task-clean-01 - remove dead artifact roundtrip_test_state.json

## Goal

`roundtrip_test_state.json` (3KB, 132 lines) sits at the repo root with no source code referencing it. It appears to be a legacy TKM test fixture. Dead files create confusion about what is active.

## Objective

Remove `roundtrip_test_state.json` after confirming it is unreferenced.

## Non-Goals

- auditing all legacy artifacts across the repo
- preserving the data elsewhere

## Documentation References

- (none needed)

## References

- `roundtrip_test_state.json`

## Exact Files To Change

- `roundtrip_test_state.json` — delete

## Files To Avoid Unless Necessary

- any file with `grep`-able reference to `roundtrip_test_state`

## Delete / Migrate Decision

- `roundtrip_test_state.json` — delete (dead artifact, no code references it)

## End State

`roundtrip_test_state.json` no longer exists in the repository.

## Exit Criteria

- `ls roundtrip_test_state.json` fails
- all tests still pass
- `git diff` shows only the deletion

## Suggested Implementation Path

1. `git rm roundtrip_test_state.json`
2. Run tests to confirm nothing breaks

## Validation

- `pytest -q`
- `test -f roundtrip_test_state.json && echo exists || echo removed`

## Failure Modes

- (very unlikely) some test or script implicitly depends on this file

# task-test-01 - expand serialization round-trip tests

## Goal

YAML persistence is a critical path (the prototype storage layer), but only 2 tests cover serialization round-trips (`test_serialization_roundtrip.py`). This is insufficient for catching data loss, metadata corruption, or compatibility regressions.

## Objective

Add round-trip tests covering representative WiGame payloads, including edge cases (empty games, full matrices, facts with evidence, legacy key compatibility).

## Non-Goals

- adding a database backend
- changing the serialization format
- testing non-YAML persistence paths

## Documentation References

- `docs/storage_boundary.md`
- `docs/data_models.md`
- `docs/operations.md`

## References

- `tests/test_serialization_roundtrip.py`
- `src/operational_model/system/wi_game_serialization.py`
- `src/operational_model/system/wigame.py`
- `examples/*.yaml`

## Exact Files To Change

- `tests/test_serialization_roundtrip.py`

## Files To Avoid Unless Necessary

- source code under `src/`
- example YAML files

## Delete / Migrate Decision

- N/A (test expansion, no migration)

## End State

At least 6-8 round-trip test cases cover: minimal WiGame, full matrix, facts with evidence, metadata preservation, legacy key fallback, and edge cases (empty axes, single cell).

## Exit Criteria

- `pytest tests/test_serialization_roundtrip.py -v` shows 6+ passing tests

## Suggested Implementation Path

1. Add test for minimal WiGame (no facts, empty matrices)
2. Add test for WiGame with full matrix of mixed truth/sense values
3. Add test for facts with evidence/metadata
4. Add test for WiGame metadata preservation
5. Add test for legacy key fallback (ejeA → axis_a)
6. Add test for edge cases (single row, single column)

## Validation

- `pytest tests/test_serialization_roundtrip.py -v`

## Failure Modes

- tests passing but not actually verifying the right things
- test data drifting from the actual serialization format

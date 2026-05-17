# task-db-04 - test YAML persistence

## Goal

Make YAML the trusted prototype persistence surface until a future database backend is needed.

## Objective

Add round-trip and schema-oriented tests that prove `WiGame` serialization preserves the operational data needed by the prototype.

## Non-Goals

- replacing YAML with SQLite or Postgres now
- introducing a repository abstraction in this task
- designing the final production storage architecture

## Documentation References

- `docs/canonical_forms_and_ingestion.md`
- `docs/data_models.md`
- `docs/operations.md`
- `docs/rebuild_and_migration_policy.md`

## References

- `src/operational_model/system/wi_game_serialization.py`
- `src/operational_model/system/wigame.py`
- `src/operational_model/core/fact.py`
- `src/operational_model/core/proposition.py`
- `tests/test_operational_model.py`

## Exact Files To Change

- `src/operational_model/system/wi_game_serialization.py`
- `tests/test_operational_model.py`
- `tests/test_status_evaluation.py` if serialization affects sense/truth cases
- `docs/canonical_forms_and_ingestion.md` only if the serialized contract changes

## Files To Avoid Unless Necessary

- `src/unified_engine.py`
- `src/tkm_orchestrator.py`
- storage backends outside YAML prototype work

## Delete / Migrate Decision

- `src/operational_model/system/wi_game_serialization.py` -> migrate
- YAML prototype persistence -> migrate
- future Postgres compatibility work -> defer

## End State

YAML round-trips can be trusted to preserve `WiGame`, `Fact`, `Proposition`, and metadata needed by the prototype, with explicit tests for compatibility and losslessness within the supported surface.

## Exit Criteria

- round-trip tests cover representative `WiGame` payloads
- serialized facts preserve proposition shape, truth, and evidence
- supported key names and compatibility shims are tested explicitly

## Suggested Implementation Path

1. Audit the current YAML payload shape and fallback behavior.
2. Add round-trip fixtures covering facts, evidence, and matrix payloads.
3. Tighten serialization only where tests reveal ambiguity or loss.
4. Keep the storage surface YAML-first and document only the supported compatibility rules.

## Validation

- `pytest tests/test_operational_model.py`
- `pytest tests/test_status_evaluation.py`
- `pytest`

## Failure Modes

- round-trip tests miss evidence or metadata loss
- compatibility fallbacks expand without a defined contract
- task drifts into full database design before the YAML prototype is solid

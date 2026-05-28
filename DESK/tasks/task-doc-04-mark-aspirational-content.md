# task-doc-04 - mark aspirational content in docs

## Goal

Multiple docs use aspirational language ("should", "intended direction", "target") without distinguishing what is implemented vs planned. A new reader cannot tell what works today.

## Objective

Add explicit status labels (`✅ Implemented`, `🔄 In progress`, `📋 Planned`) to aspirational statements across the documentation.

## Non-Goals

- rewriting the content of the docs
- auditing every sentence for accuracy
- adding new documentation sections

## Documentation References

- All docs under `docs/`

## References

- `docs/proposition_first_architecture.md`
- `docs/operations.md`
- `docs/canonical_forms_and_ingestion.md`
- `docs/kernel_symbol_policy.md`
- `docs/concepts.md`

## Exact Files To Change

- Selected doc files with aspirational language

## Files To Avoid Unless Necessary

- `docs/coding_standards.md` (prescriptive, not aspirational)

## Delete / Migrate Decision

- N/A (annotation, not migration)

## End State

Aspirational sections in the documentation are clearly labeled so readers can distinguish implemented capability from future direction.

## Exit Criteria

- `grep -n "should\|intended\|target\|future\|planned" docs/` shows labeled annotations

## Suggested Implementation Path

1. Search docs for "should", "intended", "target future", "will", "planned"
2. Add inline annotations: `✅ Implemented` for test-proven behavior, `📋 Planned` for aspirational content
3. Review with a quick test to confirm annotations match reality

## Validation

- Manual review of 3-5 annotated docs

## Failure Modes

- annotations become stale as implementation catches up
- subjective judgment about what counts as "implemented"

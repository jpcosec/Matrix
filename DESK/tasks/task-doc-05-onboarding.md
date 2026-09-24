# task-doc-05 - add developer onboarding section

## Goal

There is no onboarding guide. A new developer must piece together the architecture from 11 docs, read source to find class signatures, and guess the development workflow.

## Objective

Add a short onboarding section to either `README.md` or a new `docs/onboarding.md` covering: how to set up, how to run tests, how the package is structured, how to add a new relation/operation, and where to look for examples.

## Non-Goals

- rewriting existing docs
- adding API reference generation (sphinx/mkdocs)

## Documentation References

- `docs/architecture.md`
- `docs/data_models.md`
- `docs/operations.md`
- `docs/coding_standards.md`

## References

- `src/operational_model/` — the code the onboarding should explain

## Exact Files To Change

- `docs/onboarding.md` (new file)
- or `README.md` (add section)

## Files To Avoid Unless Necessary

- source code
- test files

## Delete / Migrate Decision

- N/A (new documentation)

## End State

A new developer can read one document and know how to set up, run tests, understand the structure, and make their first change.

## Exit Criteria

- The onboarding doc exists and is referenced from `docs/README.md`

## Suggested Implementation Path

1. Outline the sections: Setup, Running tests, Code structure, Your first change (e.g., adding a relation), Where to find examples
2. Write the guide
3. Add to `docs/README.md` reading order

## Validation

- A developer unfamiliar with the codebase can follow the guide without asking questions

## Failure Modes

- onboarding goes out of date as the codebase evolves
- too much detail (becomes another architecture doc)
- too little detail (not useful)

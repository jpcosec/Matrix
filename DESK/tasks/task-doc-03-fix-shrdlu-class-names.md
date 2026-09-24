# task-doc-03 - fix Shrdlu docs class names

## Goal

The README and docs reference `EnglishParser` and `Lowering` as Shrdlu class names, but the actual exported classes are `TokenStream` (in `english_parser.py`) and `PrototypeHarness` (in `lowering.py`). This misleads readers trying to understand or use the prototype.

## Objective

Update Shrdlu documentation to use the correct class names.

## Non-Goals

- renaming the actual source classes
- expanding Shrdlu documentation beyond fixing names

## Documentation References

- `prototypes/shrdlu/README.md`

## References

- `prototypes/shrdlu/english_parser.py` — exports `TokenStream`, not `EnglishParser`
- `prototypes/shrdlu/lowering.py` — exports `PrototypeHarness`, not `Lowering`

## Exact Files To Change

- `prototypes/shrdlu/README.md`
- `docs/proposition_first_architecture.md` (if it references Shrdlu classes)
- `docs/architecture.md` (if it references Shrdlu classes)
- `README.md` (root — if it references Shrdlu class names)

## Files To Avoid Unless Necessary

- source code under `prototypes/shrdlu/`
- source code under `src/`

## Delete / Migrate Decision

- N/A (text fixes only)

## End State

All references to Shrdlu classes use the correct exported names.

## Exit Criteria

- `grep -r "EnglishParser\|class Lowering" docs/ prototypes/ README.md` returns empty or matches only false positives

## Suggested Implementation Path

1. Search all docs for `EnglishParser` and `Lowering`
2. Replace with `TokenStream` and `PrototypeHarness` respectively
3. Search for any other wrong class names

## Validation

- `grep -rn "EnglishParser\|class Lowering" docs/ prototypes/shrdlu/ README.md`

## Failure Modes

- missing a reference in a non-obvious doc file

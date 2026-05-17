# Pill 02 - S-Expression Canonical Form

## What

The canonical external proposition representation is `(R a b)`.

`aRb` is theoretical notation only.

## Why

`(R a b)` is explicit, parseable, serializable, and extensible. `aRb` is compact but not a good storage or transport format.

## How

- Internal code uses separated fields: `relation_id`, `subject_symbol_id`, `object_symbol_id`.
- External textual form uses s-expressions.
- Documentation may use `aRb` only as philosophical shorthand.

## What For

This prevents format drift across parsing, serialization, docs, and tests.

## Applies To

- proposition serialization
- tests
- docs
- future parsers or loaders

## Does Not Apply To

- purely informal philosophical prose where `aRb` is explanatory

## Failure Modes

- storing propositions in mixed formats
- writing tests against non-canonical text forms

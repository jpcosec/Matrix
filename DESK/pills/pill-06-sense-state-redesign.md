# Pill 06 - Sense State Redesign

## What

`Si` should evolve from flat enum-like values into explicit German-named dataclass states.

## Why

The current flat shape is too lossy for the intended semantics and encourages imprecise uses of `sinnvoll`, `sinnlos`, and `unsinnig`.

## How

Target hierarchy:

- `SinnvollTatsache`
- `SinnvollUnabgebildet`
- `SinnlosTautologisch`
- `SinnlosWiderspruechlich`
- `UnsinnigFehlgebildet`
- `UnsinnigAusserhalb`

`__str__` should print the explanation in English.

## What For

This keeps semantic distinctions explicit and prevents status drift.

## Applies To

- future `Si` refactor
- status evaluation
- docs and tests about sense states

## Does Not Apply To

- temporary transitional enum storage while structural refactor is still in progress

## Failure Modes

- using `sinnlos` to mean "unmapped"
- treating `out_of_scope` as separate from `unsinnig`

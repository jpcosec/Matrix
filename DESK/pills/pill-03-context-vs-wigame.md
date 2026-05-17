# Pill 03 - Context vs WiGame

## What

`WiGame` and `Context` are not synonyms.

- `WiGame` is a local evaluative language game.
- `Context` is a routing structure that can point to `Context` or `WiGame`.

## Why

Collapsing them into one concept mixes local truth evaluation with hierarchical navigation.

## How

- Facts live in `WiGame`.
- Routing lives in `Context`.
- `Context -> Context | WiGame` is the recursive rule.

## What For

This keeps local semantics and cross-space navigation decoupled.

## Applies To

- `src/operational_model/routing/**`
- `src/operational_model/system/**`
- all routing tests

## Does Not Apply To

- legacy runtime types kept only during migration

## Failure Modes

- putting factual truth logic on `Context`
- treating `WiGame` as a generic container node

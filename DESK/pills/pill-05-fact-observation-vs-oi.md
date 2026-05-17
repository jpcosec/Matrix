# Pill 05 - Fact Observation vs Oi

## What

`Oi` should not be preserved as a first-class matrix in the new architecture.

Its intent belongs on `Fact` metadata.

## Why

Observation is a property of a fact, not a structural matrix concern by default.

## How

- do not migrate `Oi` as a matrix
- if needed, store observation semantics on `Fact`
- example fields: `observed`, `source`, `derived_from`, `confidence`

## What For

This avoids a redundant matrix layer and keeps provenance where it semantically belongs.

## Applies To

- migration decisions from `UnifiedMatrixEngine`
- future fact metadata design

## Does Not Apply To

- historical explanation of the old runtime

## Failure Modes

- recreating `Oi` only because it existed before
- mixing provenance with matrix mechanics

# Pill 04 - Legacy Migration Policy

## What

Legacy code is not maintained for its own sake.

Every legacy surface must be classified as:

- `migrate`
- `delete`
- `defer`

## Why

Without an explicit migration policy, legacy code keeps absorbing attention and contaminates the new architecture.

## How

- Migrate only behavior that the new architecture actually wants.
- Delete tests that only preserve old shapes.
- Keep deferred code only temporarily and explicitly.

## What For

This prevents accidental compatibility work from becoming architecture.

## Applies To

- `src/unified_engine.py`
- old engines
- old tests
- old orchestration helpers

## Does Not Apply To

- new operational-model modules

## Failure Modes

- keeping compatibility shims indefinitely
- migrating whole files instead of extracting only useful behavior

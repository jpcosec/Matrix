# Pill 01 - Proposition-First Ontology

## What

The system is proposition-first, not object-property-first.

The primitive logical unit is a proposition of the form `(R a b)`.

## Why

Starting from `object -> property` hides the real logical structure and collapses `b` into a special case when it is also a thing.

## How

- Model `Thing`, `Relation`, `Proposition`, and `Fact` explicitly.
- Treat `Fact` as a proposition plus truth assignment.
- Build `WiGame` on top of proposition slots, not on top of ad-hoc feature assumptions.

## What For

This keeps the code aligned with the intended Wittgensteinian model and prevents old object/property architecture from re-entering the system.

## Applies To

- `src/operational_model/**`
- all new loaders, serializers, and tests

## Does Not Apply To

- deleted legacy runtime shapes kept only in git history

## Failure Modes

- reintroducing "property" as a primitive instead of a thing in relation
- designing APIs around `(object, property)` instead of `(relation, subject, object)`

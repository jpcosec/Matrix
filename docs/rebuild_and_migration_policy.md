# Rebuild and Migration Policy

This document defines how Matrix rebuild work should interact with legacy code and how that work should be decomposed operationally.

## Legacy classification rule

Legacy code is not maintained for its own sake.

Every touched legacy surface must be classified as one of:

- `migrate`
- `delete`
- `defer`

The classification must be explicit in the task, not implied.

## Migration rule

Migrate only behavior that the new architecture actually wants.

Do not migrate whole files or preserve old abstractions unchanged. Extract the useful behavior, redesign it in terms of the proposition-first model, and leave the rest in git history.

## Deletion rule

Delete tests and helpers that exist only to preserve obsolete runtime shapes.

Compatibility work should not become architecture by inertia.

## Deferred rule

Deferred surfaces may remain temporarily, but they must stay explicitly marked and should not silently re-enter active design.

## Task granularity rule

Tasks should be as granular as possible and should expose their dependencies clearly.

Prefer tasks like:

- delete a specific set of files
- extract a named behavior into a new module
- rebuild one operation on top of the new model

Avoid tasks like:

- clean all legacy
- refactor a legacy surface wholesale
- fix everything around routing

Granular tasks reduce ambiguity, reduce context contamination, and make safe parallel execution possible.

## Task authoring rule

Each non-trivial task should list:

- exact files to change
- files to avoid unless necessary
- documentation references
- concrete validation commands
- explicit `migrate`, `delete`, or `defer` decisions for touched legacy surfaces

If a task cannot be executed from that information, the task is underspecified and should be hardened before implementation.

## Failure modes

Typical rebuild failures include:

- keeping compatibility shims indefinitely
- migrating whole files instead of extracting useful behavior
- repairing old tests without improving the new architecture
- letting one task touch unrelated surfaces without explicit need
- allowing multiple tasks to depend on unstated assumptions

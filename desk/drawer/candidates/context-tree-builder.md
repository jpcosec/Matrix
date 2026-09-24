# Build the context tree instead of hand-wiring it

ID: task-context-tree-builder
Status: deferred
Priority: medium

## Rationale

`routing/context.py` already is the search tree: `Context` holds a
`descriptor: Proposition`, `routes: list[ContextRoute]`, and
`RouteTargetKind.CONTEXT | WIGAME` distinguishes an internal node from a leaf.
`system/hypertensor.py` now walks it to assemble `WCi`.

What is missing is anything that *builds* it. `route_to_context` and
`route_to_wigame` are called by hand, one edge at a time.

## Goal

Derive the context tree from a corpus: chunks become contexts, symbol convergence
proposes identity between contexts, and gates decide what is promoted.

## Scope

New module under `src/operational_model/routing/`.

## Depends on

`task-outer-layer-numpy-scipy`. The intended mechanism already exists in the
sibling: `sia/` computes implicative intensity and cohesion (CHIC), and
`pipeline/curate.py` is explicitly "LLM-assisted curation: a backend drafts
proposals, a human still promotes". That human-in-the-loop shape is the accepted
design, not a placeholder.

## Notes

Once `task-partition-search` exists, the two meet: the search decides *where* to
cut a world, and this decides *which contexts* the cuts belong to. The tree is the
output of both.

`Context.descriptor` being a `Proposition` is what lets a context be described
rather than merely named — combined with `reflection.reify_context`, a context can
now also be the *subject* of a proposition. Both directions are available.

# Data Models

This document is an index of the operational data structures of the Matrix
framework.

## Central models

* `WiGame`: the local language-game view. Each world owns its own `V_i` / `S_i`
  matrices. There is no global hyper-store: state lives in the world.
* `LogicalSystem`: the root orchestrator and registry of dictionaries.
* `Proposition`: the canonical logical structure `(R a b)`.
* `Fact`: the proposition with an empirical truth value.
* `Symbol`: logical entity that defines the matrix axes.
* `Thing`: the operational symbol-name pair.
* `Relation`: the logical operator (the matrix's Y-axis).
* `RoutingProjection`: subject-axis projection between two `WiGame`s; non-empty
  only if they share a canonical referent.

## Deferred material

The former `Hipertensor_Canonico` model (a single global fact store backed by a
JAX tensor, of which `WiGame`s would be local views) was never built and is not
planned. See [`../desk/drawer/jax/README.md`](../desk/drawer/jax/README.md).
The `TractatusKnowledgeMachine/atoms/` atom graph this document used to point at
is not present in this repository.


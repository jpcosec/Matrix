# Two architecture specs still describe modules that do not exist

ID: task-stale-architecture-specs
Status: deferred
Priority: low

## Rationale

The JAX deferral moved out `architecture_{component,deployment,sequence,state}.*`
because they named `CanonicalHypertensor` and XLA outright. Two survived the sweep
because they contain no JAX string, but they describe the same ghost architecture:

`docs/specs/architecture_reflection.yaml` declares four modules; two do not exist:

```
OK       src/operational_model/core
OK       src/operational_model/system
FANTASMA src/operational_model/compiler
FANTASMA src/operational_model/engine
```

`docs/specs/architecture_activity.yaml` is titled "MEEL Deduction Flow" and
describes the deduction path through that same engine.

## Goal

Either rewrite both against the real package layout, or move them to
`desk/drawer/jax/docs/specs/` with the rest.

## Scope

- `docs/specs/architecture_reflection.yaml`
- `docs/specs/architecture_activity.yaml`
- `docs/specs/architecture_activity.mmd`, `architecture_state.mmd` (check for orphans)

## Notes

Rewriting is the better option for `activity`: deduction *is* real now
(`system/deduction.py`, traced modus ponens to a fixed point), so the flow it
describes exists — it just lives in `system/`, not `engine/`. `reflection` should
be regenerated from the actual tree, which now also has `kernel/`, `matrices/`,
`routing/` and `language/`.

Nothing references `docs/specs/` programmatically, so neither choice breaks a build.

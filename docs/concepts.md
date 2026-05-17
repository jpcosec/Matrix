# Concepts

Matrix combines a philosophical vocabulary about meaning with a computational model built from explicit logical contexts and matrix operations.

## Philosophical vocabulary

The project borrows from the *Tractatus Logico-Philosophicus* the idea that logical evaluation should happen over facts and their form, not only over isolated words.

- `sinnvoll`: a proposition is meaningful in context and can be evaluated as true, false, or unknown.
- `sinnlos`: a proposition collapses into tautological or contradictory structure and carries no discriminative information.
- `unsinnig`: a proposition is not applicable in the current context, so evaluation itself is ill-formed.

In the codebase, these labels are used to explain why a proposition succeeds or fails logical validation, not just whether it is true.

## MEEL and the structural masks

The MEEL layer organizes reasoning through four related masks:

- `V_i` - truth values
- `S_i` - sense or applicability
- `O_i` - observed or explicitly grounded facts
- `D_i` - discriminative capacity

This separation matters because a proposition can be false yet meaningful, or impossible to evaluate because it never applies to the target object in the first place.

## Truth values

The unified engine uses a four-valued representation through `TruthValue`:

- `TRUE`
- `FALSE`
- `UNKNOWN`
- `NOT_APPLICABLE`

That allows the engine to distinguish missing knowledge from structural invalidity.

## Information energy

`get_information_energy` measures how informative a context is based on its matrix structure.

- Code reference: `src/unified_engine.py`

Use it when comparing contexts or when deciding whether a routed view remains discriminative enough to justify further reasoning.

## Dimensional collapse and routing

The unified engine uses JAX-backed matrix operations to derive square similarity-style representations from rectangular knowledge matrices.

- `dimensional_collapse` builds local collapsed views.
- `recursive_bridge_routing` propagates information across contexts.

These operations support multi-hop reasoning, bridge traversal, and higher-level composition workflows.

- Code reference: `src/unified_engine.py`

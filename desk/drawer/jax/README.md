# JAX / CanonicalHypertensor — deferred

Abandoned architecture. Kept for the record, not for execution.

## Decision

The `CanonicalHypertensor` (a single global fact store backed by JAX tensors,
with `WiGame`s as local projections of it) was the original design. It is not
built and is not planned.

The implemented architecture instead keeps state **inside each `WiGame`**:
each world owns its own `V_i` / `S_i` matrices as plain Python nested lists,
and crossing between worlds goes through `RoutingProjection`. There is no
global tensor, and `setup.py` declares no numeric dependency (`pyyaml` only —
no `jax`, no `numpy`).

The sibling repository `matrix-shrdlu-spec` reached the same conclusion
independently and recorded it in `specs/matrix.md` and `specs/SPEC.md`:

> Hipertensor canónico global y migración a JAX (… tareas `[draft]`): no se
> hacen. El estado vive en cada `WiGame`.

## Why the tasks here are deferred rather than closed

Every task in `tasks/` scoped its work to a module that does not exist and
never did — `src/operational_hypertensor.py`, `src/operational_engine.py`,
`src/operational_compiler.py`, `src/operational_feeder.py`,
`src/operational_space.py` — and validated against JAX/XLA behaviour
("compila exitosamente en XLA", "Mintermos a (row, col) compatibles con JAX").
They are deferred because the architecture was dropped, not because the work
was finished.

## One capability was built by another route

`tasks/task-meelengine-fixpoint-deduction-algorithm.md` asked for the
recursive multiplication loop run to a fixed point. That capability exists in
the delivered engine as `src/operational_model/system/deduction.py` (traced
modus ponens over the compiled implication matrix, iterated to a fixed point,
carrying `tier`/`rule` provenance). The JAX version of it remains deferred.

## Layout

- `tasks/` — 8 task docs, `status: deferred`
- `routines/` — their routine docs, `status: archived`
- `primitives/` — their checklists, conditions, edges and operators, `status: archived`
- `pill-migracion-a-jax.md` — the migration pill, `status: deprecated`
- `canonical_hypertensor.py`, `matrix_feeder.py` — draft stubs (`import jax`; not importable here)

These files are under `desk/drawer/`, which is not a modelled desk surface, so
they are not tracked in the `.sldb` store and do not appear in the active
board.

# Drawer

Deferred desk work for Matrix lives here until it is promoted into active
execution. `desk/drawer/` is not a modelled desk surface, so nothing here is
tracked in the `.sldb` store or routed on the board.

## Contents

- **`candidates/`** — 10 loose deferred work items, one file each, with the
  evidence for why they are open. See [`candidates/README.md`](candidates/README.md)
  for the index and for how to promote one into a real task.

- **`jax/`** — the abandoned JAX / `CanonicalHypertensor` architecture: 8 task
  docs (`status: deferred`), their routines and primitives (`archived`), the
  migration pill (`deprecated`), the draft stubs and the design docs that
  described it. See [`jax/README.md`](jax/README.md).

- **`shrdlu/`** — **not deferred.** The controlled-language prototype is live and
  covered by five test modules (`test_shrdlu_english_parser`, `test_shrdlu_lexicon`,
  `test_shrdlu_lowering`, `test_shrdlu_dialog`, `test_shrdlu_spanish`). It sits here
  because it is a *prototype* on top of the engine rather than part of it, not
  because it is dormant.

  `repl.py` exposes `build_repl()`, which lazily imports `pipeline.run` and
  `populator` from the unported outer layer; calling it raises
  `ModuleNotFoundError`. Everything else in the package works standalone.
  `text_norm.py` is vendored from `populator.tokenize` so the prototype needs no
  part of that layer. See [`../../PORT_GAPS.md`](../../PORT_GAPS.md).

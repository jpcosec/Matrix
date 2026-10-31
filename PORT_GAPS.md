# Port gaps

What is still missing from the `matrix-shrdlu-spec` sibling, and why.

## Closed

The SHRDLU prototype is now complete. `spanish.py`, `repl.py` and the fuller
`dialog_state.py` were ported into `desk/drawer/shrdlu/`. Their only dependency on
the unported layer was `populator.tokenize.normalize`, a stdlib-only function now
vendored as `desk/drawer/shrdlu/text_norm.py`.

`tests/test_shrdlu_spanish.py` covers the Spanish surface and the dialogue state
by building worlds directly, instead of through `pipeline.run.build_system` as the
sibling's version did.

## Still open: the outer ingestion layer

One decision blocks all of it: this repo declares no numeric dependency
(`setup.py` installs `pyyaml` only), and the outer layer uses `numpy`/`scipy` in
13 places.

| package | LOC | what it does |
|---|---|---|
| `populator/` | 813 | documents → chunks (contexts) → local signs with offsets |
| `sia/` | 732 | CHIC: implicative intensity (ϕ), cohesion, hierarchy, AROMA |
| `pipeline/` | 2504 | sentence decomposition, per-context ingestion, convergence, routed queries, curation |
| `experiments/` | 1997 | evaluation harness |
| `specs/` | 12 docs | including `chic.md` |
| `corpus/` | 4.7 MB | 89 physicists (Simple English + EN + Wikidata + GAP) |

Consequences of not having it:

- **Contexts are built by hand.** `Context.route_to_context` and
  `route_to_wigame` must be called explicitly. The intended automation is CHIC
  plus LLM-assisted curation (`pipeline/curate.py`: a backend drafts, a human
  promotes).
- `desk/drawer/shrdlu/repl.py` keeps `build_repl()`, which lazily imports
  `pipeline.run` and `populator`. Importing the module is fine; calling
  `build_repl()` raises `ModuleNotFoundError`. Every other entry point works.
- The sibling's `test_shrdlu_repl.py` is not ported: it drives
  `pipeline.curate.FakeBackend`, `pipeline.run.build_system`,
  `pipeline.convergence.symbol_convergence` and `pipeline.decompose.decompose`.

## Unrelated to the port

`Proposition` carries exactly two symbol slots and `LiSpace` exactly two axes, so
arity is 2. See `docs/semantic_fields.md` section 10.

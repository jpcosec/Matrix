# Port the outer ingestion layer from matrix-shrdlu-spec

ID: task-outer-layer-numpy-scipy
Status: deferred
Priority: high

## Rationale

This repo is the official one but only holds the engine. The sibling at
`/home/jp/proyectos/matrix-shrdlu-spec` holds the whole text-to-WiGame pipeline,
which was never ported. Without it, contexts are built by hand: nothing infers a
partition from a corpus.

One decision blocks all of it. `setup.py` declares `install_requires=["pyyaml"]`
and the outer layer uses `numpy`/`scipy` in 13 places. Porting it means the engine
stops being dependency-free.

## Goal

Decide whether this repo is the engine only, or engine plus population pipeline.
If the latter, port the layer and declare the numeric dependencies explicitly
(ideally as an optional extra so the engine stays installable without them).

## Scope

| package | LOC | what it does |
|---|---|---|
| `populator/` | 813 | documents -> chunks (contexts) -> local signs with offsets |
| `sia/` | 732 | CHIC: implicative intensity (phi), cohesion, hierarchy, AROMA |
| `pipeline/` | 2504 | sentence decomposition, per-context ingestion, convergence, routed queries, curation |
| `experiments/` | 1997 | evaluation harness (89 physicists) |
| `specs/` | 12 docs | including `chic.md` |
| `corpus/` | 4.7 MB | Simple English + EN + Wikidata + GAP |

Out of scope: rewriting any of it. This is a port plus a dependency decision.

## Unblocks

- `task-context-tree-builder` (CHIC + LLM curation is the intended automation)
- `task-shrdlu-build-repl` (needs `pipeline.run` and `populator`)
- the sibling's `test_shrdlu_repl.py`, not portable today

## Notes

Suggested shape if accepted: `extras_require={"pipeline": ["numpy", "scipy"]}` so
`pip install -e .` keeps working for engine-only users, and the pipeline tests are
skipped when the extra is absent. That preserves the current guarantee instead of
silently dropping it.

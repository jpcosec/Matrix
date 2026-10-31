# Drawer candidates

Loose, deferred work items. Each file is a candidate, not a task: it carries
`Status: deferred` and is **not** tracked in the `.sldb` store, not routed on the
board, and not validated by any model.

A candidate becomes a task only by authoring it explicitly:

```bash
deskops add task --root . --from-drawer <file> --title "..." --goal "..." \
  --scope "..." --validation "pytest -q"
```

The drawer file is kept afterwards for manual cleanup.

## Index

| candidate | size | kind |
|---|---|---|
| `outer-layer-numpy-scipy.md` | large | decision — blocks several others |
| `partition-search.md` | medium | feature — makes the hypertensor self-organising |
| `arity-n-ary-propositions.md` | large | model change |
| `stale-architecture-specs.md` | small | cleanup |
| `deskops-scaffold-phase-md.md` | small | upstream bug report |
| `context-tree-builder.md` | medium | depends on the outer layer |
| `projection-emit-roundtrip-kb.md` | small | test coverage |
| `si-mask-authoring.md` | medium | open question |
| `shrdlu-build-repl.md` | small | depends on the outer layer |
| `order-axioms-wiring.md` | small | follow-up wiring |

Ordering in the table is by how much else each one unblocks, not by priority.

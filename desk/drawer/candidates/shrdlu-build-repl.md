# shrdlu build_repl() needs the corpus layer

ID: task-shrdlu-build-repl
Status: deferred
Priority: low

## Rationale

The SHRDLU port is otherwise complete: `spanish.py`, `repl.py` and the full
`dialog_state.py` are in `desk/drawer/shrdlu/`, and `populator.tokenize.normalize`
is vendored as `text_norm.py` (stdlib only) so the package needs nothing from the
unported layer.

One entry point still does. `repl.py:246` lazily imports `pipeline.run.build_system`
and `repl.py:251` imports `populator.read_documents`:

```python
from pipeline.run import build_system
...
from populator import read_documents
```

Importing the module is fine and every other surface works. Calling `build_repl()`
raises `ModuleNotFoundError`.

## Goal

Either port the two functions it needs, or give `build_repl()` a corpus-free path
that builds a world from an already-compiled KB.

## Scope

`desk/drawer/shrdlu/repl.py`.

## Notes

The second option is probably better and does not depend on the numpy decision: a
KB under `examples/` is already a compiled world, so a REPL could open one directly
instead of re-ingesting a corpus. That would make the prototype demonstrable from
this repo alone.

The sibling's `test_shrdlu_repl.py` stays unportable either way: it drives
`pipeline.curate.FakeBackend`, `pipeline.convergence.symbol_convergence` and
`pipeline.decompose.decompose`. See `PORT_GAPS.md`.

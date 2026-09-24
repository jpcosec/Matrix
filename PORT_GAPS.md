# PORT_GAPS.md

Missing modules referenced by copied engine tests that do NOT exist in this
repo after porting steps 1+2 (not created per task constraints):

- `pipeline.curate`
- `pipeline.run`
- `pipeline.convergence`
- `pipeline.decompose`
- `pipeline.ingest`
- `populator`
- `prototypes.shrdlu.dialog_state`
- `prototypes.shrdlu.spanish`
- `prototypes.shrdlu.repl`

Deleted test files that import the above:

- `tests/test_shrdlu_repl.py`
- `tests/test_shrdlu_spanish.py`

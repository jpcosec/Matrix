# Proto-SHRDLU

This folder contains the SHRDLU-inspired prototype language work.

It is intentionally outside `src/operational_model/` so the Matrix core can stay general.

## Scope

- structured lexicon inspired by historical `dictio.lisp`
- multiword combination handling such as `pick up` and `on top of`
- shallow controlled-English parsing into stable semantic frames
- tiny demo harness for parser experimentation

## Non-Goals

- canonical core runtime semantics
- planner parity with historical SHRDLU
- blocks-world simulation as architecture

## Demo

```bash
python prototypes/shrdlu/proto.py --once "Put the red block on the blue cube."
# or
python -m prototypes.shrdlu.proto --once "Put the red block on the blue cube."
```

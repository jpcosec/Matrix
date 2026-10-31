# Search over candidate partitions

ID: task-partition-search
Status: deferred
Priority: high

## Rationale

`system/partition.py` judges a partition you hand it. `compare_partition(composite,
parts)` returns a verdict with the deciding metric, which is the criterion — but
nothing *searches*. The hypertensor cannot organise itself while a human has to
propose every candidate cut.

This is the piece that turns the measured criterion into a procedure.

## Goal

Given a set of facts (or one wide WiGame), enumerate plausible partitions by
shared middle term and return the best one under the existing criterion, with the
route that produced it.

## Scope

`src/operational_model/system/partition_search.py` (new).

Reuses, does not duplicate:
- `routing/middle_term.middle_terms` to find the join candidates
- `system/partition.score_wigame` / `compare_partition` for the verdict
- `system/shape_guard.diagnose_shape` to reject degenerate candidates outright

## Implementation path

Candidate generation is the real design question. A wide world over
`subjects x objects` can be split at any object that also appears as a subject
elsewhere, so the candidate set is bounded by the middle terms actually present,
not by all subsets. That keeps it tractable: enumerate middle terms, build the two
parts implied by each, score, keep the best.

Beam search over successive splits gives the tree rather than one cut.

## Validation

- on the `grosor_hoja` family the search finds the `tiene_parte` + `grosor` split
  without being told the middle term
- a world with no shared middle term yields no split and says so
- candidates flagged `error` by `shape_guard` are never returned
- deterministic: same facts, same partition

## Done when

Given the vegetable facts and nothing else, the search proposes the same split
that `compare_partition` currently has to be handed.

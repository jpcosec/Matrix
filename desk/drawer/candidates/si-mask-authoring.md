# Where does S_i come from?

ID: task-si-mask-authoring
Status: deferred
Priority: medium

## Rationale

`S_i` is load-bearing everywhere now. It gates routing
(`middle_term.compose` breaks a chain on a sinnlos leg), it gates the operational
matrix (`BlockMatrix.evaluate_operational`), it gates emission
(`matrix_to_s_expressions` skips TRUE-but-sinnlos cells), and it carries the
Wittgenstein distinction the whole model rests on.

But nothing authors it. `SiMatrix.pure()` fills everything `sinnvoll`, and from
there it is set cell by cell. In practice every world starts fully meaningful,
which is the opposite of the claim that sense is contextual and local.

`docs/operatoria_recetas.md` documents the intended source: an authored domain
operatoria declares which operations apply, and `Si=0` (`unsinnig`) marks what does
not apply to the domain. `tools/kb/operatoria/*.yaml` is a worked example. That
mechanism exists for recipes and nowhere else.

## Goal

Decide and document how `S_i` is populated in general: authored per domain,
inferred from the relation's algebra and axes, or proposed and curated.

## Open question, not a spec

Three candidate sources, not mutually exclusive:

1. **Authored operatoria** — what recipes do today. Precise, does not scale.
2. **Derived from the algebra** — an `irreflexive` relation makes the diagonal
   `unsinnig` mechanically; `requires_distinct_operands()` already reports this and
   nothing consumes it. Cheap and sound as far as it goes.
3. **Proposed and curated** — `system/candidates.py` already has the queue and the
   `tier`/`curation` vocabulary for exactly this shape.

Option 2 is free and available right now: wiring
`RelationAlgebra.requires_distinct_operands()` into `SiMatrix` construction would
make self-application senseless by default for order relations. That alone is worth
doing independently of the larger question.

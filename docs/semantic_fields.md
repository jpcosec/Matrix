# Semantic fields: order, the middle term, reflection and quantification

How the engine gets from an unordered set of `(R a b)` cells to something you can
project back out as language. This document is the design record for four
capabilities that were added together, and for the three measurements that
decided their shape.

The framing throughout: **the hypertensor is a search tree.** Each node is a
closed `W_i`, each parent routes to its children, and the cut points are chosen
by discriminative power. `routing/context.py` is that tree; the rest of this
document is what makes its nodes well formed.

---

## 1. Why a matrix alone projects nothing

`V_i` is truth over `axis_a × axis_b` and `S_i` is applicability over the same
space. Read a cell and you get one `(R a b)`. Read them all and you get a **set**
of propositions: no order, no sequence, no comparison, no quantifier.

That is enough to answer "is this true here" and not enough to say anything. The
four gaps below are what stood between the matrices and a faithful projection.

---

## 2. Order (`core/relations/relation_algebra.py`, `core/relations/order.py`)

### The problem

`RelationAlgebra` exposed four booleans: `transitive`, `associative`,
`distributive`, `commutative`. With only those you cannot tell a transitive
relation from an order, because you have no antisymmetry and no totality. Worse,
`commutative` — symmetry, `(R a b) ≡ (R b a)` — is the **exact opposite** of an
order axiom. The vocabulary could not express the thing.

### What was added

Three axioms, all defaulting to `False` so every legacy call site is unchanged:

| axiom | meaning |
|---|---|
| `irreflexive` | `(R a a)` is not admissible |
| `antisymmetric` | `(R a b)` and `(R b a)` cannot both hold for `a ≠ b` |
| `total` | for distinct `a`, `b`, one direction must hold |

Classifiers: `is_strict_partial_order()` (transitive ∧ irreflexive ∧
antisymmetric), `is_total_order()` (that, plus total), `requires_distinct_operands()`.

`validate_pairs(pairs)` enforces only the axioms the profile declares and raises a
`ValueError` **naming the violated axiom**.

### Order over edges

`core/relations/order.py` works on plain `(nodes, edges)` with no dependency on
`WiGame` or the algebra:

- `assert_acyclic` — raises naming the cycle: `cycle: picar -> sofreir -> ... -> picar`
- `topological_sequence` / `linear_extension` — deterministic linear extension,
  ties broken by position in `nodes`
- `is_total` — **judged on the transitive closure**

That last choice matters. A chain declared by its covering edges
(`picar → sofreir → … → servir`) has no direct edge from `picar` to `servir`, so
by direct edges it is not total — yet it plainly is a total order. Totality is a
property of the order, not of the diagram you drew it with.

### Measured

```
declared order : ['picar','sofreir','desglasar','agregar_caldo','cocinar_lento','servir']
recovered order: ['picar','sofreir','desglasar','agregar_caldo','cocinar_lento','servir']  match: True
is_total       : True
cycle rejected : cycle: picar -> sofreir -> desglasar -> agregar_caldo -> cocinar_lento -> servir -> picar
```

---

## 3. The middle term (`routing/middle_term.py`)

### The problem

`RoutingProjection` joins **subject axis to subject axis**. That is not where two
worlds meet. Two worlds meet at the **middle term**: a symbol that is an *object*
of the first and a *subject* of the second.

```
(debe legumbre guisarse)      W1: axis_a=[legumbre]  axis_b=[guisarse]
(necesita guisarse fuego)     W2: axis_a=[guisarse]  axis_b=[fuego]
                                               ^^^^^^^^ the middle term
```

`core/transitive_inference.py` cannot chain these: it filters by `relation_id`, so
two different relations never meet. Before this module, nothing composed across
`guisarse`.

### The contract

```python
middle_terms(w1, w2)  -> list[str]                    # w1.axis_b ∩ w2.axis_a
compose(w1, w2)       -> list[tuple[str, str, str]]   # (subject, middle, object)
compose_pairs(w1, w2) -> list[tuple[str, str]]        # (subject, object)
```

Two invariants:

1. **Sense gates routing.** A leg holds only when its cell is `TRUE` in `V_i`
   **and** `sinnvoll` in `S_i`. A leg that is true but senseless breaks the chain.
   This is the Wittgenstein constraint applied to traversal, not just to storage.
2. **The middle term stays explicit** in the triple. The route is auditable; you
   can always say *why* `legumbre` reaches `fuego`.

No symbol and no relation is ever created. Composition observes, it does not
invent.

### Why this is a subset

Object→subject is one join among many. The widest possible world would allow any
cell to join any other, and that world is exactly the degenerate one described
next. The restriction is the feature.

---

## 4. Shape guards (`system/shape_guard.py`)

### The problem

The widest `W_i` you can build fills up with propositions like:

```
(* pedrito es_hermano_de_maria)
```

Two pathologies in one cell. The relation `*` constrains nothing, so the world
states no move shape. And the object `es_hermano_de_maria` **packs a relation and
an argument into a single symbol**, so `maria` stops being a symbol and becomes a
substring. You can no longer ask who Pedrito is a brother of: the answer is inside
a string, unindexable.

### Measured

```
W universal    r='*'             3x6 = 18 cells, 1 fact, E=0.5278
W factored     r=es_hermano_de   3x3 =  9 cells, 3 facts, E=0.5556
```

The degenerate world scores worse on energy while costing **twice** the cells. But
the score is not the point — the *shape* is. A world can score fine and still be
malformed, which is why this is a separate diagnosis and not a threshold on `E`.

### The findings

| kind | severity | catches |
|---|---|---|
| `wildcard_relation` | error | `*`, empty, `any`, `rel` — relations that admit anything |
| `packed_object` | error | a label embedding a registered symbol; **names the trapped symbol** |
| `conjunctive_object` | warning | `es_hermano_de_maria_y_alto` — two facts in one cell |
| `non_discriminative_column` | warning | tautological columns: no `D_i` contribution |
| `sparse_world` | warning | axes wider than the knowledge in them |

`is_well_shaped()` rejects on errors only: a tautological column is a smell, a
packed object is a defect.

`packed_object` detection needs the system registry — that is what distinguishes
`es_hermano_de_maria` from an ordinary compound label. Without a system it is
skipped rather than guessed.

---

## 5. The hypertensor, assembled (`system/hypertensor.py`)

### What already existed

`matrices/block_matrix.py` implemented the omnirepresentation and
`to_global_matrix()` folded it into one labelled matrix:

```
        contexts   facts
    ctx [  WCi   |  Si  ]
    sub [  Si^T  |  Vi  ]
```

Routing between contexts and truth inside worlds, in one object, with labelled
axes. What was missing: **anybody building it from a real system.** It was only
ever constructed inside its own unit test.

### What was added

`assemble_block_matrix(system)` walks the `Context` routing tree for `WCi` and
stacks the routed worlds for `S_i` and `V_i`.

Labels are qualified `"<wigame_id>::<symbol>"`, and `unqualify()` reverses it.
This is not cosmetic: `hoja` can be a subject in two different worlds, and
collapsing them would destroy exactly the distinction that contexts exist to
preserve. **The hypertensor must not lose the indexing of symbols.**

### A latent bug this exposed

`BlockMatrix.evaluate_operational()` did:

```python
return self.truth_matrix.elementwise_and(self.sense_matrix)
```

`elementwise_and` requires identical axes. But the class declares `Si` as
`context × terms` and `Vi` as `subjects × terms`. **Those never share a row
axis**, so the method could not work with the shapes the class itself declares.

It went unnoticed because nothing ever called it, and its own test — named
`test_block_matrix_builds_global_and_operational` — never exercised the
operational half.

Fixed by joining over the shared axis (the terms) instead of assuming aligned
rows, with an optional `context_id` to gate by one context's sense row. A term is
admissible under a context only if that context routes to the world owning it.

---

## 6. Partition: `E(R)` and `D_i` as a criterion (`system/partition.py`)

### The problem

`information_energy()` and `tautological_columns()` were computed and read by
nobody. The only consumer was `tools/kb/capabilities.py`, asserting that the
energy **is a float**. Dead numbers.

### The measurement that changed the criterion

The intuition under test: the best shape is the one with least entropy, so
`r = grosor_hoja` should lose against `r1 = tiene_parte` + `r2 = grosor`.

```
                          3 subjects              300 subjects
composite  grosor_hoja    3x2 =   6, E=0.6250     300x2 = 600
part 1     tiene_parte    3x1 =   3, E=0.7500     300x1 = 300   taut=('hoja',)
part 2     grosor         1x2 =   2, E=0.6250       1x2 =   2
                        -----------              -----------
split total                      5                      302
```

The split does win — but **not because of entropy**. Splitting *introduces* a
tautological column: every plant has a leaf, so `hoja` discriminates nothing and
`D_i` drops to zero for that world. Energy alone would argue against it.

What pays is **reuse of the middle term**. The composite grows as
`subjects × values`; the split grows as `subjects × 1` plus a constant
`middle × values`. The advantage widens from 1 cell to 298.

So the criterion is: **cells are the cost, `D_i` is the quality, and middle-term
reuse is what makes the cost scale sublinearly.** Not minimum entropy.

### The API

`score_wigame()` returns size, density, energy, tautological columns and
discriminative power. `compare_partition(composite, parts)` returns a
`PartitionVerdict` carrying `choice`, `reason` and — importantly — `metric`, the
name of what decided it. A verdict that cannot say why is not a criterion.

---

## 7. Quantification (`kernel/rule_schema.py`)

### The problem

Rules were **ground**, and `tests/test_deduction.py` admitted it in a comment. The
rule `(if (es x verdura) (es x comestible))` has `x` as the literal symbol `"x"`,
with a `Thing(Symbol("x"))` registered so it would resolve. That is not a schema;
it is one fact-shaped rule. "Every vegetable is edible" needed one rule per
symbol, written by hand.

No variables, no unification, no quantifiers existed anywhere in `src/`.

### The approach: source transformation, not a new engine

A variable is any atom starting with `?`. A `RuleSchema` carries variables;
`expand()` grounds it against the symbols actually present in the worlds; and the
existing ground machinery (`RuleMatrixCompiler`, `system/deduction.py`) runs
**completely unchanged**.

This is deliberate. Nothing downstream learns about variables, so the matrix
semantics, the implication-matrix closure and the provenance chain all keep
working exactly as before. Quantification is added at the edge, where it costs
nothing.

```python
schema = parse_schema("(if (es ?x verdura) (es ?x comestible))")
schema.variables          # ('?x',)
system.rules.extend(expand_for_system(schema, system))
deduce(system)            # derives for lechuga AND acelga
```

`expand()` is deterministic and deduplicated; the universe comes from the union of
the worlds' axes. Multiple variables expand over the product. An unbound variable
left after `substitute()` is fine — partial grounding is allowed — but `bind()`
requires every variable and names the ones missing.

Verified: the derivation fires for both vegetables and **no `x` symbol is ever
registered**. The schema did the quantifying.

---

## 8. Reflection (`system/reflection.py`)

### The problem

`LogicalSystem.relations` and `LogicalSystem.things` are **disjoint registries**.
A relation id lives in one, symbols in the other, and nothing links them:

```
(persigue pedrito maria)     'persigue'  is a relation id  → system.relations
(es perseguir verbo)         'perseguir' is a symbol       → system.things
```

`'persigue' in system.things` was `False`. There was no way to ask *what kind of
thing is the relation I just used*. The same gap blocked predicating over a
context, since `WiGame.context_id` is a bare `str | None`.

### The approach: reification with reversible namespaces

A relation gets a mirror symbol `rel:<id>`; a context gets `ctx:<id>`. The mirror
is a real registered `Thing`, so it can sit on an axis and be the subject of a
meta-level proposition — while the relation keeps working as a relation.

```python
reify_relation(system, "persigue")        # registers Thing(Symbol("rel:persigue"))
# now this world is well formed:
LiSpace("li:meta", ["rel:persigue"], ["verbo"], "es")
relation_of_symbol(system, "rel:persigue")   # -> Relation(relation_id='persigue')
```

The registries stay separate. What is new is a **declared, reversible
correspondence** rather than a collapse of the two spaces. `dereference()` goes
back, and `describes()` returns `None` for a mirror with nothing behind it, so a
dangling meta-symbol is detectable rather than silently accepted.

This makes the `(es pedrito pulento)` + `(contexto_palabra pulento chileno)` case
expressible: the word-context level is just another world, whose subjects happen
to be reified.

---

## 9. What the four cases do now

| case | status |
|---|---|
| `(es gato animal)` + `(es animal ser_vivo)` | already worked — transitive closure |
| `(debe legumbre guisarse)` + `(necesita guisarse fuego)` | `middle_term.compose()` |
| `(persigue pedrito maria)` + `(es perseguir verbo)` | `reflection.reify_relation()` |
| `(es pedrito pulento)` + `(contexto_palabra pulento chileno)` | `reflection.reify_context()` |
| "every vegetable is edible" as one rule | `rule_schema.parse_schema()` |

---

## 10. Still open

**Contexts are built by hand.** `Context.route_to_context` / `route_to_wigame` are
called explicitly; nothing infers the partition. The intended path is CHIC plus
LLM-assisted curation, which exists in the unported `matrix-shrdlu-spec` outer
layer (`sia/` for implicative intensity and cohesion, `specs/chic.md`,
`pipeline/curate.py` where a backend drafts and a human promotes). Bringing it
over means accepting `numpy`/`scipy`, which today the engine does not depend on.

**Arity is still 2.** `Proposition` has exactly `subject_symbol_id` and
`object_symbol_id`; `LiSpace` has exactly two axes; the matrices are 2-D. Ternary
propositions are not representable and reification is the only workaround. This
matters much less now that relations can be reified, but it is not closed.

**`compare_partition` compares a proposal.** It judges a split you hand it; it
does not search for the split. The search over candidate partitions is the next
real piece, and it is what would finally make the hypertensor self-organising.

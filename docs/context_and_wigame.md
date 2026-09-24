# WiGame, Context and Disambiguation

This document states the constitutive role of the context in a `WiGame`, why
sense (`Si`) is contextual, and how accumulating contexts disambiguates a
symbol.

## The claim

A `WiGame` is **(axes + relation) under a context**, not a pair of axes alone.

- The relation fixes the admissible move shape `(R a b)`.
- The axes fix which terms can occupy each position.
- The **context** fixes *which* admissible moves are meaningful and true here.

Change the context and the same relation over the same surface terms is a
different game. Two WiGames with equal axes and relation but different contexts
are not the same object.

## Local sense

- `Si` is not a manual list of absurdities: it is the local admissibility mask of
  a context. A term is addressable *here* or it is not.
- `unsinnig` means "outside this context", not "false".
- Consequently a sign such as `she` can be `sinnvoll` inside `ctx:marie_curie`
  and `unsinnig` in a context where the referent was never introduced.

## Contexts form a tree

- `Context` is a routing node. It routes to subcontexts (`ContextRoute` with
  `target_kind=CONTEXT`) or to `WiGame` leaves (`target_kind=WIGAME`).
- Deeper contexts refine the admissible coordinates. Context refinement is how
  the system avoids one flat, exploding space.
- `WiGame.context_id` records the leaf's context; a WiGame without a context is
  under-specified.

```
ctx:kb
└── ctx:marie_curie
    ├── wigame:marie_curie:es
    └── wigame:marie_curie:nace_en
```

## Why accumulating contexts disambiguates

Each added context contributes constraints. A symbol does not carry meaning by
itself: what it denotes is the **path/leaf** where its occurrences converge.

1. With one context, `she` is an ambiguous leaf.
2. With N contexts about the same domain, each additional fact splits the
   candidate set (`D_i`, the discriminative dimension).
3. The referent is the intersection that survives every context's constraints.
4. The string stops mattering; what matters is the semantic field the occurrence
   indicates.

This is the operational reading of `Colapso_Dimensional` and
`Juego_de_Desambiguacion`: collision detection plus either a discriminative
dimension or a subcontext refinement, minimizing information energy `E(R)`.

## Cross-context identity is curation, not string matching

- `RoutingProjection` links subject axes of two WiGames. Shared canonical
  referents across contexts are what make a projection non-empty.
- Deciding that `she@marie_curie` and `curie@marie_curie` denote the same
  referent is a **reviewed decision**, not an automatic normalization.
- Aliasing per context is how a referent survives across contexts without
  pretending that surface identity implies referential identity.

## Storage consequence

Facts are context-scoped coordinates. The same `(R a b)` asserted in two
articles yields two facts in two contexts, and may be truth-linked by a
projection. Collapsing them into one global cell destroys exactly the structure
that disambiguates.

The canonical direction of the architecture is therefore not a global facts
store. The former `Hipertensor_Canonico` design — one global tensor from which
`WiGame`s would be extracted as local views — was never built and is abandoned;
see [`../desk/drawer/jax/README.md`](../desk/drawer/jax/README.md).

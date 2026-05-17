# Data Models

This repository now distinguishes between local language games and higher-order routing structures. The operational base lives in `src/operational_model/`.

## First principles

- The primary datum is the proposition, not the object/property pair.
- A proposition has the form `(R a b)`.
- A fact is a proposition with a truth assignment.
- A `WiGame` is a local language game where propositions are evaluated.
- A `Context` is a routing node that can point to `WiGame` instances or to other `Context` instances.
- Each `WiGame` serializes directly as `ejeA`, `ejeB`, `relacion`, `contexto`, `Vi`, and `Si`.

## `Name`

`Name` is the sign that designates a thing in language.

- Field: `sign`
- Optional field: `namespace`

For the current system, the sign is usually a string.

## `Symbol`

`Symbol` is not treated as a closed atom. It is modeled as a differential construction supported by facts and `WiGame` occurrences.

Fields:

- `symbol_id` - stable logical identifier
- `signs` - all known signs that designate the symbol
- `supporting_fact_ids` - facts currently supporting the symbol
- `supporting_wigame_ids` - `WiGame` instances where those supports appear

This reflects the idea that the mapping from sign to symbol is always partial and revisable.

## `Thing`

`Thing` is the operational pair `symbol/name`.

Fields:

- `symbol`
- `name`
- `aliases`

`Thing` is the entity used in propositions as `a` or `b`.

## `Relation`

`Relation` is the logical operator `R` in `(R a b)`.

Fields:

- `relation_id`
- `name`
- logical properties such as `transitive`, `associative`, `distributive`, `commutative`

Relations are not uniform labels; each one can declare its own semantics.

## `Proposition`

`Proposition` is the base logical form.

Fields:

- `relation_id`
- `subject_symbol_id`
- `object_symbol_id`
- `wigame_id`
- `proposition_id`

It represents a possible configuration inside a `WiGame` but carries no truth by itself.

## `Fact`

`Fact` is a proposition with a truth value.

Fields:

- `proposition`
- `truth`
- `fact_id`

This is the first evaluable unit of the system.

## `LiSpace`

`LiSpace` defines the index structure that supports a `WiGame`.

Fields:

- `axis_a`
- `axis_b`
- `relation_id`

Operationally, it determines which propositions are well-formed for that game.

## `BooleanMatrix`

`BooleanMatrix` is the shared matrix base class used by the operational layer.

Fields:

- `row_axis`
- `column_axis`
- `values`

It provides indexed access, row/column extraction, and direct serialization.

## `ViMatrix`

`ViMatrix` inherits from `BooleanMatrix` and stores truth values for a `WiGame`.

- rows correspond to `ejeA`
- columns correspond to `ejeB`
- cells store `true`, `false`, or `unknown`

`ViMatrix` also exposes tautology detection and subject matching against `p_i`.

## `SiMatrix`

`SiMatrix` inherits from `BooleanMatrix` and stores sense values for a `WiGame`.

- rows correspond to `ejeA`
- columns correspond to `ejeB`
- cells store `sinnvoll`, `sinnlos`, or `unsinnig`

`SiMatrix` is the operational source for checking whether a game remains pure.

## `WiGame`

`WiGame` is the local language game where propositions and facts live.

Fields:

- `li`
- `context_id`
- `propositions`
- `facts`
- `Vi`
- `Si`

It exposes:

- `search(p_i)` -> local search over `Vi` constrained by `Si`
- `is_pure()` -> whether the game avoids `unsinnig`
- `tautological_columns()` -> dimensions that do not discriminate locally
- `to_dict()` / `to_yaml()` -> direct serialization of the game and its matrices

By default:

- declared propositions with facts are usually `sinnvoll`
- declared but unevaluated positions remain `sinnlos`
- malformed propositions are `unsinnig`

## `SearchVector (p_i)`

`SearchVector` is the query vector inside a `WiGame`.

- it lives on the `ejeB` axis of a game
- it marks which terms are being requested
- it is evaluated against `Vi`, while `Si` prevents malformed matches

Operationally, `p_i` answers: what am I looking for inside this game?

## `ContextRoute`

`ContextRoute` is a directed routing edge.

Fields:

- `source_context_id`
- `target_kind` -> `context` or `wigame`
- `target_id`
- `relation_id`

## `Context`

`Context` is not just another `WiGame`. It is a higher-order routing node.

It can point to:

- another `Context`
- a `WiGame`

This makes the hierarchy recursive:

- `Context -> Context | WiGame`

`Context` is responsible for semantic navigation and hierarchical descent toward more specific language games.

## `RoutingProjection (r_i)`

`RoutingProjection` inherits from `BooleanMatrix` and represents a projection between two `WiGame` spaces.

- rows belong to the source `WiGame`
- columns belong to the target `WiGame`
- `True` marks that a source subject projects to a target subject

This is the concrete operator used for crossings such as:

- `W_animales_es_propiedades x r_proyeccion_animales_caninos x W_caninos_es_propiedades`

Operationally, `r_i` answers: how do the subjects of one game project into another?

## `LogicalSystem`

`LogicalSystem` is the aggregate root for the operational model.

It registers and links:

- names
- symbols
- things
- relations
- `LiSpace`
- `WiGame`
- `Context`
- `RoutingProjection`

When a fact is added through the system, symbol support is updated automatically so that symbols remain grounded in the evolving set of facts.
The system also exposes local search and cross-search using `p_i` and `r_i`.

## Design consequence

With this model, the system no longer starts from `object -> property`. It starts from:

- `Thing`
- `Relation`
- `Proposition`
- `Fact`
- `LiSpace`
- `BooleanMatrix`
- `ViMatrix`
- `SiMatrix`
- `SearchVector`
- `WiGame`
- `Context`
- `RoutingProjection`

That is the intended operational base for future refactors of the older engines.

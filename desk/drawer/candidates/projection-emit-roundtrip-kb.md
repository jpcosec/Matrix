# Round-trip a versioned KB through the projection

ID: task-projection-emit-roundtrip-kb
Status: deferred
Priority: low

## Rationale

`task-proyeccion-wigame-y-matrices-a-s-expressions` said "Done when: a KB from
examples/ is emitted to s-expressions and re-ingesting reproduces the same facts".
What shipped is the round trip on a hand-built world: emit 14 lines, feed them to
`SExpressionRuntime` on a fresh `LogicalSystem`, every line returns `accept`, the
world is rebuilt.

The `examples/` half was never done. The versioned KBs
(`examples/kb_wikipedia_10_articles`, `kb_wikipedia_marie_curie`) are real
extraction output with aliases and projections, which is a harder and more honest
case than a fixture.

## Goal

Emit a versioned KB from `examples/` through `wigame_to_s_expressions`, re-ingest,
and assert fact-set equality.

## Scope

`tests/` plus possibly a small helper. Must not modify anything under `examples/`:
those are versioned extraction results, not regenerable artifacts.

## Validation

- every emitted line evaluates to `accept`
- the re-ingested fact set equals the original, compared on `(R a b)` per WiGame
- aliases and `RoutingProjection` survive or the gap is documented explicitly

## Notes

Expect this to find real gaps rather than pass first try. `wigame_to_s_expressions`
emits `create relation / create symbol / create li / create wigame / assert`, and a
KB carries aliases, contexts and projections that are not in that list. Whatever it
cannot express is exactly the finding.

# KB: Marie Curie (versionada)

Un solo artículo, curado a mano: el ejemplo más chico que muestra el ciclo
completo (propuestas → revisión → alias → WiGame context-scoped → query).

## Qué está versionado

- `proposals/*.jsonl` — propuestas por relación (9 WiGames).
- `review.yaml` — ledger (todas aprobadas).
- `aliases.yaml` — `she`/`curie`/`maria`/`marie` → `marie_curie` en el contexto `marie_curie`.
- `relations.yaml`, `manifest.yaml`, `sources/marie_curie.json`.

## Cómo materializarla offline

```bash
python -m tools.kb --kb examples/kb_wikipedia_marie_curie compile
python -m tools.kb --kb examples/kb_wikipedia_marie_curie verify --fail-on-problems
python -m tools.kb --kb examples/kb_wikipedia_marie_curie query \
    "(check wigame:marie_curie:premio (premio marie_curie nobel_prize_in_physics))" \
    "(check wigame:marie_curie:nace_en (nace_en marie_curie warsaw))"
python -m tools.kb --kb examples/kb_wikipedia_marie_curie contexts
```

Resultado esperado: 71 facts, 4 WiGames, `verify` ok, ambas proposiciones `true`
(la segunda sólo existe gracias a la curación de alias: el worker había extraído `Curie`).

Digest: `examples/reports/wikipedia_marie_curie.digest.json`.

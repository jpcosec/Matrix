# KB: 10 artículos de Wikipedia (versionada)

Extraction results (LLM) preserved so the KB is queryable offline without
re-running workers. Esto es lo **no regenerable**: la corrida de extracción.

## Qué está versionado

- `proposals/*.jsonl` — propuestas aceptadas por contexto y relación (salida de `ingest` sobre los candidatos de los workers).
- `review.yaml` — ledger de revisión (todas aprobadas con reviewer y nota).
- `aliases.yaml` — curación de ocurrencias: `she`/`curie`/`maria`/apellidos → referente del contexto.
- `relations.yaml` — vocabulario y álgebra usada.
- `manifest.yaml` — snapshot con totales y hashes de la corrida original.
- `sources/*.json` — metadata de cada artículo (título, URL, revid, sha256 del texto).

No versionado (regenerable): `facts/`, `wigames/`, `contexts.yaml`, `projections/`, `shared.yaml`, `symbols.yaml`.

## Cómo materializarla offline

```bash
python -m tools.kb --kb examples/kb_wikipedia_10_articles compile
python -m tools.kb --kb examples/kb_wikipedia_10_articles verify --fail-on-problems
python -m tools.kb --kb examples/kb_wikipedia_10_articles query \
    "(check wigame:niels_bohr:descubierto_por (descubierto_por nuclear_fission otto_hahn))"
python -m tools.kb --kb examples/kb_wikipedia_10_articles shared --symbol polonium
```

Resultado esperado: 693 facts, 11 contextos (10 artículos + raíz), 102 WiGames, 50 proyecciones; `verify` ok.

## Origen

Artículos: Marie Curie, Pierre Curie, Irène Joliot-Curie, Lise Meitner, Otto Hahn,
Rosalind Franklin, James Watson, Francis Crick, Albert Einstein, Niels Bohr.
Extracción: 165 workers `pi` + `deepseek-flash` (1 por chunk), luego `ingest` + revisión + curación.

Digest: `examples/reports/wikipedia_10_articles.digest.json`.

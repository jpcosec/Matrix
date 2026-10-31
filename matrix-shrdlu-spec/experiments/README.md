# `experiments/` — evaluación sobre el corpus de físicos

Ejecuta el pipeline completo (populator → descompositor → ingesta por contexto → convergencia) sobre
`corpus/physicists` (89 físicos: artículo de Simple English + artículo completo de la Wikipedia
inglesa + hechos de Wikidata + GAP) y mide convergencia y consultas ruteadas por régimen y
descompositor. Qué significa cada número está en
[`../specs/convergence.md`](../specs/convergence.md) §7.

## Reglas de ejecución

- Toda corrida va **con tope de memoria** y `timeout` explícito:
  `bash scripts/capped.sh 4 -- <comando>` (cgroup transitorio con `MemoryMax=4G`, sin swap).
  El 2026-09-20 tres corridas sin tope mataron el scope de la terminal por OOM.
- **Una corrida por comando**, cada una con su `--out`. Nunca encadenar evaluaciones en un `for`.
- Nunca `p×p`: la intensidad se calcula sobre pares candidatos (índice invertido configuración →
  símbolos) y la convergencia entra por lotes. Ver [`../.herdr/briefs/_reglas.md`](../.herdr/briefs/_reglas.md).

```bash
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer heuristic --out /tmp/eval/pairs_heuristic
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer llm       --out /tmp/eval/pairs_llm
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer both      --out /tmp/eval/pairs_both
```

## Regímenes y descompositores

| Flag | Qué hace |
|---|---|
| `--regime document` | un contexto por artículo; con `--source simple` (89 ctx) o `--source en` (89 ctx) |
| `--regime section --unit section` | un contexto por sección `## H` del artículo EN (564 ctx) |
| `--regime pairs` | los **dos contextos por físico**: artículo Simple + lead EN (178 ctx); `--with-sections` añade además las secciones EN |
| `--decomposer heuristic` | declaraciones por patrones (`pipeline/decompose.py`), sin red |
| `--decomposer llm` | declaraciones del LLM desde la caché por chunk (`corpus/physicists/declarations_llm.jsonl`) |
| `--decomposer both` | une heurística y LLM |
| `--limit N` | solo los primeros N contextos |
| `--max-memory-gb 4` | `RLIMIT_AS` del proceso (además del cgroup de `capped.sh`) |
| `--taxonomy` | construye además el árbol de contextos (`context_taxonomy(max_features=600)`; es lo lento) |
| `--out <dir>` | destino de `metrics.json` y `report.md` |

La caché del LLM se llena **una vez** (≈11 min con 8 workers; después 0 llamadas, la evaluación es
offline):

```bash
bash scripts/capped.sh 4 -- python -m pipeline.decompose_batch corpus/physicists --regime pairs --backend pi --workers 8
```

## Qué mide `metrics.json`

- `world`: contextos, símbolos, hechos, variables (≥ 2 declaraciones), promovidos / propuestos /
  referentes, aislados, pares candidatos y lotes.
- `pairs`: convergencia entre fuentes (personas), desglose pronombre↔pronombre / etiqueta↔etiqueta /
  pronombre↔etiqueta, ejemplos y los 10 fallos con sus configuraciones compartidas.
- `intra_context`: contextos donde el pronombre y la etiqueta del mismo artículo convergen.
- `ranking`: MRR / hit@1 / hit@3 sobre **todas** las consultas del régimen — las consultas sin
  candidato correcto entre los pares (`unranked`) aportan 0, y se reportan aparte; comparar MRR sin
  mirar `ranked`/`unranked` engaña.
- `qa` / `qa_pairs` / `qa_pronoun_subject`: recall y precision contra Wikidata (etiqueta y con salto
  Simple→EN).
- `garbage`: 50 hechos plantados (deben quedar aislados) frente a 50 hechos reales.
- `false_merges`: convergencias entre qids distintos sin mención cruzada.
- `tautological_configurations`: configuraciones descartadas por aparecer en más de `taut_df=0.30`
  de los contextos (no discriminan identidad).
- `gap`: cobertura del dataset GAP sobre el corpus.
- `timings`: segundos por etapa y `peak_memory_mb`.

`metrics.json` se escribe parcialmente tras cada etapa, así que una corrida interrumpida conserva lo
medido hasta ahí. `report.md` resume lo mismo en prosa con las tablas de pares y fallos.

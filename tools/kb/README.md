# tools/kb — KB fan-out harness

Convierte texto, código o specs en una KB de Matrix (`WiGame`s context-scoped),
con validación determinista, revisión obligatoria y verificación reproducible.

- Modelo de contexto: [`docs/context_and_wigame.md`](../../docs/context_and_wigame.md)
- Arquitectura, mediciones y stress: [`docs/kb_fanout_harness.md`](../../docs/kb_fanout_harness.md)
- Operatoria de dominio: [`docs/operatoria_recetas.md`](../../docs/operatoria_recetas.md)
- Uso como skill: [`.pi/skills/matrix-kb-fanout/SKILL.md`](../../.pi/skills/matrix-kb-fanout/SKILL.md)
- Ejemplos listos para consultar: [`examples/README.md`](../../examples/README.md)

## Principios

1. **El subagente propone, el humano/agente revisa, el motor compila.** Los workers sólo escriben JSONL de candidatos; nada entra a la KB sin decisión de revisión.
2. **Todo es context-scoped.** Un `WiGame` es (ejes + relación) **bajo un contexto**; el mismo `(R a b)` en dos contextos son dos hechos.
3. **La extracción puede ser LLM o determinista.** Texto → workers free; código → AST; procedimientos → specs autoradas.
4. **Lo derivable no se versiona.** `facts/`, `wigames/`, `contexts.yaml`, `projections/`, `shared.yaml` se reconstruyen con `compile`.
5. **El álgebra se declara, no se adivina.** La operatoria de dominio dice qué cierra transitivamente y qué operaciones son admisibles.

## Mapa de módulos

| módulo | responsabilidad |
|---|---|
| `cli.py`, `__main__.py` | superficie de comandos (`python -m tools.kb`) |
| `store.py` | layout de la KB, hashing, JSONL/YAML, `slugify`, ids deterministas |
| `sources.py` | fetch de Wikipedia, chunking, prompts de worker |
| `ingest.py` | validación determinista de candidatos → **propuestas** |
| `review.py` | ledger de revisión (`kb/review.yaml`), checklist, filtros |
| `aliases.py` → `aliases` en CLI | curación `(contexto, símbolo) → referente` |
| `compile.py` | aprobadas → WiGames + contextos + alias + proyecciones + álgebra |
| `runtime.py` | `load_system`, `query`, `route`, `verify`, `report`, `contexts` |
| `software.py` | corpus de software por AST (contexto = módulo) |
| `operatoria.py` + `operatoria/*.yaml` | álgebra/operaciones/errores por dominio |
| `machine.py` + `machines/*.yaml` | specs de FSM y recetas → candidatos |
| `reach.py` | alcanzabilidad vs oráculo BFS, ciclos, inalcanzables, equivalencias |
| `capabilities.py` | 26 chequeos de upserts/inferencia/queries/sentido/serialización/kernel |
| `stress.py`, `stresswiki.py` | stress sintético y real (DBpedia) con curva de desambiguación |

## CLI

Todos los comandos aceptan `--kb <dir>` (default `kb`). Salida JSON.

### Corpus de texto (Wikipedia/artículos)

| comando | qué hace |
|---|---|
| `fetch "<título>" [--lang en] [--intro-only]` | baja plaintext + revid + sha256 a `kb/sources/` |
| `prepare [--source S] [--max-chars 1500]` | chunkea y escribe un prompt self-contained por chunk |
| `workers --source S` | imprime el plan de dispatch (chunk → prompt → output) |
| `ingest [--min-confidence 0] [--resolve drop\|last\|true\|false]` | valida candidatos y emite propuestas `pending` |

Contrato del worker (está en cada prompt): `sentence` verbatim del chunk,
`subject`/`object` presentes en la oración, `relation` del vocabulario,
`truth` booleano, sin auto-referencia, sólo JSONL.

Fan-out: `bash examples/fanout.sh <kb> [paralelo]` (usa `pi -p` con el modelo
por default, hoy `deepseek-flash`).

### Revisión

| comando | qué hace |
|---|---|
| `proposals [--status pending\|approved\|rejected\|all] [--relation R] [--limit N] [--full]` | lista propuestas con su estado |
| `review list` | alias de `proposals` |
| `review approve <id…> [--reviewer X] [--note ""]` | aprueba (acepta prefijos únicos de `proposal:`) |
| `review reject <id…> [--reviewer X] --note "motivo"` | rechaza |
| `review all --decision approved\|rejected [--status pending] [--relation R]` | decisión masiva filtrada |
| `review apply <archivo.jsonl\|yaml>` | aplica decisiones en lote (revisión asistida por otro agente) |
| `review reset [<id…>]` | vuelve a `pending` |
| `review render [--limit N]` | escribe `review_pending.md` (checklist humano) |
| `review summary` | conteos por estado y relación |
| `aliases --add '<ctx>:<símbolo>=<referente>' [--list]` | curación de ocurrencias (pronombres, apellidos, homónimos de código) |

### Materialización y consulta

| comando | qué hace |
|---|---|
| `compile [--allow-unreviewed] [--max-projection-pairs 2000]` | sólo `approved` → `wigames/`, `contexts.yaml`, `projections/`, `shared.yaml`, `facts_derived.jsonl` |
| `verify [--fail-on-problems]` | re-chequea cada hecho por `SExpressionRuntime`; valida `context_id`, contextos y proyecciones |
| `query "<sexpr>" …` | evalúa `check`/`return facts`/`ingest`/`assert` |
| `contexts` | árbol de contextos con sus WiGames |
| `route --source W --terms a,b --projections P1,P2 [--target-terms x,y]` | búsqueda multi-hop cruzando contextos |
| `shared [--symbol S] [--relation R] [--axis subject\|object]` | símbolos compartidos por ≥2 contextos (cross-contexto real) |
| `report` | agrega ingest/compile/review/verify/contextos/proyecciones |

### Corpus no-textuales

| comando | qué hace |
|---|---|
| `software --path <dir> [--path <dir>…] [--base .] [--include-tests] [--all-imports]` | AST → `define_en`, `usa`, `importa`, `hereda_de` (contexto = módulo) |
| `machine [--spec-dir tools/kb/machines] [--operatoria-dir tools/kb/operatoria]` | specs → `precede`, `requiere`, `usa`, `produce`, `sustituye_a` + contexto `operatoria` |
| `reachability [--context C] [--relation precede]` | cierre vs BFS, ciclos, inalcanzables, clases de equivalencia |
| `capabilities` | 26 chequeos del motor (upserts, inferencia, queries, sentido, serialización, kernel, KB) |

### Stress

| comando | qué hace |
|---|---|
| `stress --contexts N --relations R --shared-refs S …` | KB sintética con ground truth: costos y curva de desambiguación |
| `stress --mode wikipedia [--source dbpedia\|wikipedia] --category "<cat>" --limit N` | corpus real (contexto = categoría, referente = persona, perfil = sus categorías) |

## Layout de la KB

```
kb/
  sources/<slug>.{json,txt}      # fuente + sha256 + revid
  work/<slug>/<idx>.{txt,prompt.md}, index.json
  candidates/<slug>/<idx>.jsonl  # salida cruda de los workers
  proposals/<ctx>__<rel>.jsonl   # propuestas deduplicadas (estado en el ledger)
  review.yaml                    # decisiones (reviewer, note, reviewed_at)
  review_pending.md              # checklist
  aliases.yaml                   # curación (contexto, símbolo) -> referente
  operatoria.yaml                # álgebra/operaciones/errores del dominio
  facts/<wigame>.jsonl           # hechos aprobados + derivados
  facts_derived.jsonl            # sólo cierres/simetrizaciones
  rejects.jsonl conflicts.jsonl conflicts_after_alias.jsonl
  symbols.yaml                   # ocurrencias por contexto
  contexts.yaml projections/ shared.yaml
  wigames/<ctx>__<rel>.yaml      # KB materializada
  manifest.yaml *_report.json
```

## Gates

| gate | comando | criterio |
|---|---|---|
| Contrato | `ingest` | `unparseable`/`rejected` con motivo por fila |
| Contexto | `contexts` | 1 contexto por fuente; WiGames con `context_id` |
| Revisión | `review summary` | nada `pending` se cuela (`excluded.pending`) |
| Identidad | `aliases` + `projections/` | alias revisados; proyecciones sólo por referente compartido |
| Álgebra | `reachability` | cierre del motor == oráculo BFS |
| Reproducible | `verify --fail-on-problems` | `ok: true`, `problems: []` |

## Extender

- **Nuevo vocabulario de relaciones**: editá `tools/kb/relations.yaml` y re-corré `prepare` (regenera prompts).
- **Nuevo dominio secuencial**: agregá `tools/kb/operatoria/<dominio>.yaml` (relaciones, álgebra, operaciones, errores) y specs en `tools/kb/machines/`.
- **Nuevo corpus**: implementá un generador que escriba `work/<ctx>/000.txt` + `candidates/<ctx>/000.jsonl` (ver `software.py` y `machine.py` como plantilla) y reusá `ingest → review → compile`.
- **Nuevo chequeo**: agregá un grupo en `capabilities.py` devolviendo `{capability, ok, …evidence}`.

## Troubleshooting

| síntoma | causa / acción |
|---|---|
| `unparseable JSONL line` en `rejects.jsonl` | el worker emitió prosa o fences; `ingest` no aborta, la fila queda rechazada |
| propuestas que no aparecen | `review.yaml` dice `rejected`, o el `--status` del listado no coincide |
| `compile` con 0 facts | hay `pending` sin aprobar (`excluded.pending`), o `aliases.yaml` fusionó con conflicto (`conflicts_after_alias.jsonl`) |
| `projections_truncated: true` | se alcanzó `--max-projection-pairs` (la generación es O(contextos²)) |
| `KeyError: unknown search terms` | `SearchVector` exige términos del eje `axis_b` del WiGame consultado |
| `verify` con problemas | el WiGame YAML se editó a mano; regenerá con `compile` |
| stress real con 429 | Wikipedia API limita bajo ráfaga; usá `--source dbpedia` |

## Validación

```bash
bash examples/regenerate.sh          # KB de máquinas + demo + digest + tests
python -m pytest -q                  # suite completa (133 tests)
python -m tools.kb --kb kb capabilities
python -m tools.kb --kb kb reachability
python -m tools.kb --kb kb verify --fail-on-problems
```

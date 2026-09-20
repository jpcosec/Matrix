---
name: matrix-kb-fanout
description: Soltar subagentes libres que leen texto (Wikipedia u otra fuente), extraen proposiciones (R a b) como PROPUESTAS y las guardan en una KB de Matrix (WiGames YAML) con revisión obligatoria, validación determinista y verificación reproducible. Usar al poblar, extender o auditar la knowledge base del runtime Matrix.
---

# Matrix KB fan-out

Convierte texto plano en WiGames de Matrix. Los subagentes baratos/libres **solo proponen**; nada entra a la KB sin revisión explícita.

## Boundary

- Matrix KB = `WiGame` = **(ejes + relación) BAJO UN CONTEXTO**. No es solo un par de ejes: el contexto (el artículo/fuente) es parte de la identidad. Ver `docs/context_and_wigame.md`.
- Cada WiGame se indexa `wigame:<contexto>:<relación>` con `context_id=ctx:<contexto>`. Los contextos forman un árbol (`ctx:kb` → `ctx:<fuente>` → hojas WiGame).
- El mismo `(R a b)` en dos artículos son **dos hechos en dos contextos**, no un hecho global. La identidad entre contextos se decide por revisión (`kb/aliases.yaml`) y se materializa con `RoutingProjection`.
- Los subagentes **solo** escriben JSONL de candidatos. Nunca editan `kb/`, ni compilan, ni revisan, ni tocan `src/`.
- `ingest` convierte candidatos válidos en **propuestas `pending`** (context-scoped). La KB no cambia.
- `compile` solo materializa propuestas **`approved`**; `pending`/`rejected` se excluyen y se reportan.
- La verdad persistida es `kb/wigames/*.yaml`; el store es reproducible desde `kb/sources` + `kb/candidates` + `kb/review.yaml` + `kb/aliases.yaml`.

## Pipeline

```bash
# --- corpus de texto (Wikipedia/artículos) ---
python -m tools.kb --kb kb fetch "Marie Curie"            # o --intro-only para el resumen
python -m tools.kb --kb kb prepare --max-chars 2500       # chunk + prompt por chunk
# 1. SOLTAR SUBAGENTES: 1 worker por prompt -> kb/candidates/<slug>/<idx>.jsonl
python -m tools.kb --kb kb ingest --min-confidence 0.0    # candidatos -> propuestas pending
python -m tools.kb --kb kb review render                  # review_pending.md para revisar
python -m tools.kb --kb kb proposals --limit 20           # o listar pending por CLI
python -m tools.kb --kb kb review all --decision approved --relation premio --reviewer jp
python -m tools.kb --kb kb review reject proposal:abcdef1234 --reviewer jp --note "no taxonómico"
python -m tools.kb --kb kb compile                        # solo approved
python -m tools.kb --kb kb verify --fail-on-problems
python -m tools.kb --kb kb report

# --- corpus de software (contexto = módulo, extracción AST, sin LLM) ---
python -m tools.kb --kb kb software --path src/operational_model --path tests --base .
python -m tools.kb --kb kb ingest && python -m tools.kb --kb kb review all --decision approved --reviewer ast
python -m tools.kb --kb kb compile && python -m tools.kb --kb kb verify --fail-on-problems

# --- corpus secuencial (operatoria + FSM/recetas, specs autoradas) ---
python -m tools.kb --kb kb machine
python -m tools.kb --kb kb ingest && python -m tools.kb --kb kb review all --decision approved --reviewer operatoria
python -m tools.kb --kb kb compile                      # aplica el álgebra declarada (cierre transitivo)
python -m tools.kb --kb kb reachability                 # cierre vs oráculo BFS, ciclos, inalcanzables, equivalencias
python -m tools.kb --kb kb shared --symbol cebolla      # referentes compartidos entre contextos
```

## Dispatch de subagentes

- `prepare` genera `kb/work/<slug>/<idx>.prompt.md` (self-contained) y `kb/work/<slug>/index.json`.
- Listá el plan: `python -m tools.kb --kb kb workers --source dog`.
- Lanzá **un worker por chunk** (paralelo). Cada worker lee su `.prompt.md` y escribe **solo** `kb/candidates/<slug>/<idx>.jsonl`.
- En este setup, el worker es `pi` (default `deepseek-flash`):
  `pi -p --provider deepseek --model deepseek-flash --no-tools --no-session --no-skills "$(cat <prompt>)" > <output>`
- Cualquier modelo free/barato sirve: el prompt es mecánico y las reglas duras se verifican después.
- Para orquestar panes/agentes interactivos, cargá `agent-coordinator` (herdr). Para delegación con gates, `deskops-task-lifecycle`.
- No interpretes la salida del worker: si un JSONL falla, queda en `kb/rejects.jsonl` con motivo.

### Contrato del worker (ya incluido en cada prompt)

```json
{"relation":"es","subject":"Dog","object":"mammal","truth":true,"sentence":"The dog is a mammal.","source":"dog","chunk_id":"dog/000","revid":1373199537,"confidence":0.9}
```

Reglas duras (deterministas, verificadas en `ingest`):
1. `sentence` debe ser subcadena **verbatim** del chunk declarado.
2. `subject` y `object` deben aparecer literalmente (word-boundary, case-insensitive) en `sentence`.
3. `relation` debe estar en `tools/kb/relations.yaml` (o en `kb/relations.yaml`).
4. `truth` booleano; `confidence` en [0,1]; sin auto-referencia; una proposición por línea.
5. Escribir solo JSONL, sin fences ni prosa. Si no hay nada: archivo vacío.

Ampliar vocabulario: editá `tools/kb/relations.yaml` y re-corré `prepare` (regenera prompts).

## Review gate

- Estado por propuesta: `pending` (default) → `approved` | `rejected`. Ledger en `kb/review.yaml` (reviewer, note, reviewed_at).
- IDs deterministas `proposal:<hash>`; se aceptan prefijos únicos.
- Comandos:
  ```bash
  python -m tools.kb --kb kb proposals --status pending [--relation <R>] [--limit N]
  python -m tools.kb --kb kb review approve <id...>   [--reviewer X] [--note "..."]
  python -m tools.kb --kb kb review reject  <id...>   [--reviewer X] --note "motivo"
  python -m tools.kb --kb kb review all --decision approved|rejected [--status pending] [--relation R]
  python -m tools.kb --kb kb review apply <decisions.jsonl|yaml>
  python -m tools.kb --kb kb review reset [<id...>]     # vuelve a pending
  python -m tools.kb --kb kb review render              # checklist Markdown
  python -m tools.kb --kb kb review summary
  ```
- Revisión batch/asistida: `review render` → un revisor (humano u otro agente) produce `{"proposal_id","decision","note"}` y se aplica con `review apply`.
- `compile --allow-unreviewed` existe solo para inspección: incluye `pending` y queda auditado en `facts` (`review.decision: unreviewed`). No usarlo como default.

## Layout de la KB

```
kb/
  sources/<slug>.{json,txt}      # fetch determinista + sha256 + revid
  work/<slug>/<idx>.{txt,prompt.md} + index.json
  candidates/<slug>/<idx>.jsonl  # salida cruda de subagentes
  proposals/<ctx>__<rel>.jsonl   # propuestas deduplicadas por contexto, status del ledger
  review.yaml                    # ledger de decisiones (reviewer, note, reviewed_at)
  review_pending.md              # checklist para revisar
  aliases.yaml                   # CURAción: (contexto, símbolo) -> referente canónico  facts/<wigame>.jsonl           # SOLO aprobadas, context-scoped
  rejects.jsonl / conflicts.jsonl / conflicts_after_alias.jsonl
  symbols.yaml                   # índice de ocurrencias POR CONTEXTO
  relations.yaml
  contexts.yaml                  # árbol de contextos + hojas WiGame
  projections/*.yaml             # links cross-contexto por referente compartido
  wigames/<ctx>__<rel>.yaml      # KB compilada (Vi/Si/facts, con context_id)
  manifest.yaml ingest_report.json compile_report.json verify_report.json
```

## Desambiguación (por qué importa el contexto)

- El signo no fija el referente: `she`, `curie`, `marie` pueden coexistir en un artículo. Eso es un **estado válido**, no un bug.
- Cada contexto nuevo aporta restricciones; el referente es la intersección que sobrevive. Ahí está la desambiguación por acumulación (ver átomo `WiGame_Contexto_y_Desambiguacion`).
- `kb/aliases.yaml` es la curación revisada, contexto-scoped:
  ```yaml
  aliases:
    - {context: marie_curie, symbol: she, canonical: marie_curie}
    - {context: marie_curie, symbol: curie, canonical: marie_curie}
  ```
- `compile` aplica alias por contexto, re-deduplica, y emite `RoutingProjection` entre contextos que comparten un referente canónico. Si dos ocurrencias fusionan con `truth` opuesto, van a `conflicts_after_alias.jsonl`.
- Interacción cross-contexto (ids de proyección `proj:<ctxA>:<ctxB>:<rel>`, sin `->`):
  ```bash
  python -m tools.kb --kb kb contexts
  python -m tools.kb --kb kb route --source wigame:marie_curie:muere_en --terms france \
      --projections proj:marie_curie:pierre_curie:muere_en --target-terms 1934
  ```

## Stress-test de escala

Los `ContextRoute`/`RoutingProjection` recién se vuelven interesantes con muchos contextos y WiGames. Hay dos modos: **sintético** (control total, ground truth inventado) y **corpus real** (DBpedia/Wikipedia, topología real, sin LLM).

```bash
# sintético: mide mecanismo + costos con parámetros controlados
python -m tools.kb --kb kb stress --contexts 250 --relations 4 --own-refs 8 \
    --shared-refs 40 --contexts-per-shared-ref 8 --root kb/stress

# real: categorías de DBpedia como contextos, categorías de cada persona como perfil
python -m tools.kb --kb kb stress --mode wikipedia --source dbpedia \
    --category "20th-century women scientists" --limit 600 --max-contexts 200 \
    --attrs-per-member 2 --root kb/stress
```

En modo real: **contexto = categoría**, **referente = persona**, **perfil = sus categorías**; dentro del contexto C cada miembro afirma hasta `--attrs-per-member` categorías propias (sampleado determinista). La superficie de homonimia es el **apellido real**. El fetch de DBpedia es una sola query SPARQL, cacheada en `raw_dbpedia.json` (reproducible offline). `--source wikipedia` existe pero requiere pacing lento (429).

Ambos modos miden:

1. **Ingeniería:** `ingest`/`compile`/`load_system`/`verify` en segundos, RSS pico, MB en disco, **ruteo cold vs hot**, y si las proyecciones se truncan.
2. **Epistemología:** curva `contexts_per_referent -> rate`: la intersección acumulada debe dejar sólo al referente verdadero entre sus homónimos.

### Sintético (250 contextos, 4640 facts, 995 WiGames)

| métrica | valor |
|---|---|
| ingest / compile / verify | 0.5s / 6.4s / 7.3s |
| `load_system` (cold) | 7.0s |
| ruteo **hot** p50 / p95 | 0.012ms / 0.016ms |
| ruteo **cold** | ~7.1s (== `load_system`) |
| proyecciones | 2000 (cap) |
| RSS / disco | 96MB / 13MB |
| curva | k=1: 52% → k=2: 91% → k=3: 99.6% → k=4: 100% |

### Real — DBpedia "20th-century women scientists" (172 personas, 200 categorías, 1498 facts)

| métrica | valor |
|---|---|
| ingest / compile / verify | 0.27s / 4.1s / 5.6s |
| `load_system` (cold) / ruteo hot p50 | 5.8s / 0.010ms |
| proyecciones | 2000 (cap, `truncated: true`) |
| RSS / disco | 66MB / 8.4MB |
| curva (attrs=2 por contexto) | k=1: 83% → k=2: 100% (survivors 1.17 → 1.0) |

Interpretación:

- La desambiguación por acumulación se sostiene con datos reales: los homónimos de apellido se separan al acumular categorías de contextos distintos.
- El cuello de botella **no** es el ruteo ni la matriz de proyección: es la hidratación total (cold ≈ 5.8s) y la generación cuadrática de pares (cap 2000). Optimizaciones obvias: cargar una vez / carga por subgrafo, y proyecciones dispersas o por demanda.
- Cap deliberado: `compile --max-projection-pairs` (default 2000).

## Operatoria y máquinas de estado

Contenido secuencial = máquina de estados. Mapeo: `Vi[estado][estado]` = transición; `Si` = guarda; `precede` asimétrico y transitivo; contexto = programa/receta/circuito.

- Specs autoradas (no extraídas): `tools/kb/operatoria/*.yaml` (relaciones, álgebra, operaciones, errores) y `tools/kb/machines/*.yaml` (FSM y recetas).
- La operatoria se materializa como contexto propio (`ctx:operatoria` → `wigame:operatoria:declara`): la spec es consultable.
- `compile` aplica el álgebra: `precede`/`sustituye_a` transitivos ⇒ hechos derivados en `facts_derived.jsonl`; `paralelo_con` conmutativo ⇒ simetrización.
- `reachability` compara el cierre del motor contra un oráculo BFS y reporta ciclos, estados inalcanzables y clases de equivalencia (usa aristas **crudas**: el cierre colapsaría todas las firmas).
- `shared` lista símbolos compartidos por ≥2 contextos en cualquier eje (los ingredientes viven en el eje de objetos; `RoutingProjection` sólo proyecta sujetos).

Resultado de referencia: recetas acíclicas con cierre derivado; `trafico` con ciclo esperado, `verde_peatonal` inalcanzable y equivalente a `verde`; acuerdo total con el oráculo BFS; `(sustituye_a manteca margarina)` derivado.

## Verificación e interacción

- `verify` re-chequea **cada hecho aprobado** vía `SExpressionRuntime` (`(check wigame:<ctx>:<rel> (<rel> a b))`), valida `context_id`, cuenta contextos y proyecciones, y emite sha256 por WiGame.
- `ingest` reporta `unparseable/accepted/proposals/rejected/conflicts` + `contexts`, y deja motivo por fila en `rejects.jsonl`.
- Conflictos: dentro de un contexto, contradicción (`true`+`false`) va a `conflicts.jsonl`. **Entre contextos distintos no hay conflicto**: son dos contextos, y se vinculan por proyección.
- Interacción sobre lo aprobado:
  ```bash
  python -m tools.kb --kb kb query "(check wigame:marie_curie:es (es marie_curie physicist))" "(return facts symbol:marie_curie)"
  python -m tools.kb --kb kb contexts
  python -m tools.kb --kb kb report
  ```
- Uso programático: `load_system(kb)` en `tools/kb/runtime.py` devuelve un `LogicalSystem` con símbolos, relaciones, WiGames, árbol de `Context` y `RoutingProjection` registrados.

## Gates de calidad

| Gate | Comando | Criterio |
|---|---|---|
| Cobertura | `workers --source <slug>` | 1 prompt y 1 output por chunk |
| Contrato | `ingest` | `unparseable` y `rejected` con motivo |
| Contexto | `contexts` | 1 contexto por fuente; WiGames con `context_id`; árbol `ctx:kb` → `ctx:<fuente>` |
| Consistencia | `ingest` | `conflicts` intra-contexto revisado, no silencioso |
| **Revisión** | `review summary` | nada `pending` se cuela: `compile` reporta `excluded.pending` |
| Materialización | `compile` | 1 WiGame por (contexto, relación) aprobada |
| Identidad | `aliases.yaml` + `projections/` | alias revisados; proyecciones solo por referente compartido |
| Reproducible | `verify --fail-on-problems` | `ok: true`, `problems: []` |

## Capacidades verificadas (`capabilities`)

`python -m tools.kb --kb kb capabilities` (escribe `capabilities_report.json`). Batería de 26 chequeos: **26 passed** también sobre la KB de software.

| grupo | qué verifica |
|---|---|
| `upserts` (5) | alta de fact, duplicado idempotente, `assert` sobre celda `false` → reject `widerspruechlich`, `ingest` sin verdad (`Vi=∅`), `set_sense` override |
| `inference` (4) | conmutativa, clausura transitiva, sin álgebra no infiere, y `WiGame.add_fact` **no** aplica álgebra (sólo `LogicalSystem.add_fact`) |
| `queries` (7) | `SearchVector`, `check` verdad/reject fuera de `Li`, `get_status`, `cross_search`, `route_search` multi-hop |
| `sense` (3) | `is_pure`, columnas tautológicas, `information_energy` |
| `serialization` (1) | roundtrip `to_yaml`/`from_yaml` de `WiGame` |
| `kernel` (2) | `parse_formula` + `collect_atoms` + `evaluate_formula` |
| `kb` (4) | todo WiGame tiene `context_id`, pronombres resueltos, proyecciones, árbol con raíz |

Gaps registrados: `search` con término inexistente lanza `KeyError`; homónimos de código (`post_init` en 4 clases) requieren curación por símbolo calificado.

## Anti-patrones

- No compilar `pending` como si estuviera aprobado; `--allow-unreviewed` es solo para inspección.
- No aplanar contextos: `wigame:<relación>` sin contexto destruye la desambiguación.
- No fusionar automáticamente `she`/`curie`/`marie`: eso es curación revisada en `aliases.yaml`.
- No dejar que un worker escriba varios archivos, compile, revise, o toque `src/`.
- No editar `kb/review.yaml` a mano si existe `review approve|reject|apply`.
- No bajar `--min-confidence` para "que pase": arreglá el prompt.
- No editar `kb/wigames/*.yaml` ni `kb/projections/*.yaml` a mano; regenerá desde `sources` + `candidates` + `review` + `aliases`.
- No dejar que una relación absorba proposiciones fuera de su semántica (`es` recibiendo `warsaw -> capital_of_congress_poland`): endurecé el prompt o separá la relación.
- Ojo: `compile` no aplica inferencia (commutativa/transitiva); `LogicalSystem.add_fact` sí, pero el KB se arma con `WiGame.add_fact`.
- No mezclar esto con deskops/SLDB (otra KB distinta).

## Validación

```bash
bash examples/regenerate.sh            # KB de máquinas + digest + tests (determinístico)
python -m pytest -q                    # suite completa
python -m tools.kb --kb kb review summary
python -m tools.kb --kb kb verify --fail-on-problems
python -m tools.kb --kb kb reachability
python -m tools.kb --kb kb capabilities
```

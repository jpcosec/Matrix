# Documentación técnica

Referencia del código de este repositorio: qué hace cada módulo, qué estructuras usa, cómo se
ejecuta y qué midió. El diseño vigente está en `specs/convergence.md`; el motor lógico es el
motor en `../src/` (raíz de este repo).

## 1. Alcance

El repositorio implementa la capa que va de texto a propuestas para Matrix:

1. trocea documentos en **contextos** e indexa los signos donde ocurren;
2. descompone oraciones en declaraciones candidatas `(R a b)` por contexto;
3. las ingiere como hechos del juego `WiGame(contexto, R)`;
4. calcula **propuestas** con SIA/CHIC: jerarquía de contextos, vínculos entre ocurrencias de
   contextos distintos, compuertas y discriminantes por juego;
5. responde consultas ruteadas con cita.

Las propuestas no son decisiones. La decisión (qué símbolo ocupa una ocurrencia, qué propuesta se
aprueba) corresponde a un intérprete que lee, LLM o persona, en una compuerta de revisión. Ese
circuito no está implementado aquí salvo `pipeline/curate.py`.

## 2. Estructura

```
populator/          documentos → chunks → signos locales con offsets
pipeline/
  decompose.py        oración → Declaration (heurística o LLM)
  llm_cache.py        caché JSONL de declaraciones LLM
  decompose_batch.py  llena la caché en paralelo
  ingest.py           declaraciones → WiGame(ctx, R); build_world
  convergence.py      jerarquía de contextos, vínculos entre ocurrencias, mantenimiento
  query.py            ask(): consulta ruteada con cita
  curate.py           cola de propuestas para un LLM revisor
  run.py              build_system: envoltorio para el REPL
sia/                contingencia, intensidad, cohesión, jerarquía, similitud, AROMA
../src/             motor booleano y runtime S-expr
../desk/drawer/shrdlu/   REPL (español e inglés controlado)
corpus/physicists/  corpus de evaluación y su build.py
corpus/vegetales/   corpus del ejemplo lechuga/espinaca
experiments/        eval_physicists.py, eval_matrix_kb.py
scripts/capped.sh   ejecutor con tope de memoria
tests/              tests de esta carpeta; motor en ../tests/
specs/              especificación (convergence.md prevalece)
.herdr/             briefs e informes por etapa de los workers
```

## 3. Flujo de datos

```
*.md ─► chunk_documents ─► Chunk ─► build_context ─► ContextIndex (signos, oraciones, offsets)
                                                          │
                                        decompose / cached_decompose
                                                          ▼
                                                   list[Declaration]
                                                          │
                                                   ingest_contexts
                                                          ▼
                              system: Context, Symbol, WiGame(ctx, R), Fact(evidence)
                                                          │
                     context_taxonomy   converge_in_batches   maintain_wigame
                                                          ▼
                               Taxonomy      ConvergenceReport      Maintenance
                                                          │
                                                        ask()
```

## 4. Estructuras de datos

| Tipo | Módulo | Campos |
|---|---|---|
| `Chunk` | `populator/contexts.py` | `ctx_id`, `document_id`, `title`, `text`, `char_offset`, `metadata` |
| `LocalSign` | idem | `sign`, `norm`, `ctx_id`, `occurrences[(sentence_index, span)]`, `kind ∈ {name, pronoun, term}` |
| `ContextIndex` | idem | `chunk`, `sentences`, `signs` |
| `Declaration` | `pipeline/decompose.py` | `ctx_id`, `relation`, `a`, `b`, `a_sign`, `b_sign`, `sentence_index`, `span`, `source ∈ {heuristic, llm}` |
| `IngestReport` | `pipeline/ingest.py` | `contexts`, `symbols`, `wigames`, `asserted`, `rejected`, `by_relation` |
| `Taxonomy` | `pipeline/convergence.py` | `nodes`, `membership`, `nests`, `levels`, `features`, `context_nodes`, `parents` |
| `PairScores` | idem | `symbols`, `rows`, `cols`, `phi`, `n_st`, `oversized` (arreglos 1-D) |
| `ConvergenceReport` | idem | `referents`, `proposed`, `promoted`, `isolated`, `scores`, `pair_scores`, `candidate_scores`, `candidates_count`, `tautological_configurations`, `processed`, `batches`, `iterations`, `ref_counter` |
| `Maintenance` | idem | `wigame_id`, `gates`, `collisions`, `discriminants`, `unresolved` |
| `Answer` | `pipeline/query.py` | `relation`, `subject`, `objects`, `path`, `explicit_false` |
| `Contingency` / `PairContingency` | `sia/contingency.py` | `n`, `n_a`, (`n_b`), `n_ab`, `n_anb`, `n_nb`; densa p×p / 1-D por par |

Identificadores:

- contexto: `<stem>` (documento) o `<stem>#<n>` (sección; `#0` es el encabezado);
- ocurrencia indexada: `norm.replace(" ", "_") + "@" + ctx_id`, p. ej. `she@Q7186`. En el código se
  guarda como `Symbol` del motor. Es una dirección de ocurrencia, no un símbolo lógico: un mismo
  signo puede denotar varios símbolos y el código trata cada `signo@ctx` como un solo nodo;
- juego: `wigame:<ctx_id>:<relation>`;
- configuración: `"<relation>|a|<ref(b)>"` o `"<relation>|b|<ref(a)>"`, donde `ref(x)` es el referente
  ya agrupado de `x` o, si no hay, su `norm`.

Cada hecho ingerido lleva `evidence = {prov: (document, span, extractor), tier: observed,
curation: confirmed}` y pertenece solo al juego de su contexto.

## 5. Módulos

### 5.1 `populator/contexts.py`

- `chunk_documents(docs, unit="document"|"section")`. En `section`, el encabezado es `stem#0` y cada
  `## ` abre `stem#n`; `###` no parte. El título de una sección es `"<artículo> — <encabezado>"`.
- `build_contexts(docs, unit, lang)` → `list[ContextIndex]`.
- Signos `name`: ventanas de hasta 6 tokens con mayúscula, admiten conectores (`of, de, the, van,
  von, y, and, …`) y apóstrofos, no cruzan puntuación. `pronoun`: siempre signo, nunca se resuelve.
  El `stem` del archivo no es signo.
- `SignIndex`: signo → contextos. Solo para enrutar consultas.
- `populator/extract.split_sentences` no corta en `;` ni dentro de paréntesis.

### 5.2 `pipeline/decompose.py`

- `RELATION_FAMILIES`: `instance`, `has_property`, `born_in`, `died_in`, `citizen_of`, `field`,
  `award`, `educated_at`, `employer`, … más relaciones abiertas `rel:<verbo>`.
- `decompose_heuristic(ctx, lang)`: cópula (núcleo del SN → `instance`, modificadores →
  `has_property`, `field` si el modificador es una disciplina), `born/died (on|in) <fecha> in <lugar>`,
  premios (además emite la variante canónica `nobel_prize`), `employer`, y `rel:<verbo>` solo con
  verbo plausible. Usa el verbo más temprano de la oración y hasta 3 cláusulas.
- `decompose_llm_chunk(ctx, backend, lang, attempts)`: una llamada por chunk. El prompt lleva título,
  oraciones numeradas, la lista cerrada de signos locales y las familias. Respuesta esperada:
  `[{"s": <nº oración>, "r": "...", "a_sign": "...", "b_sign": "..."}]`. Se descarta toda tripleta con
  un signo que no esté en la lista o una relación no permitida. No resuelve pronombres. Un reintento
  si el JSON no parsea.
- `decompose(ctx, lang, backend)`: despacha según haya backend.

### 5.3 `pipeline/llm_cache.py`, `decompose_batch.py`

- Caché: `corpus/physicists/declarations_llm.jsonl`, una línea por chunk:
  `{"key": sha1(texto), "ctx_id", "declarations": [...]}`. `cached_decompose` no llama al backend si
  la clave existe.
- `fill_cache(contexts, backend, path, workers)`: `ThreadPoolExecutor`; registra por chunk
  declaraciones, descartes y tiempo; salta el chunk tras dos fallos.
- Backend: `pipeline.curate.PiBackend(model="deepseek/deepseek-flash", timeout=180, thinking="off")`;
  `FakeBackend` para tests.

### 5.4 `pipeline/ingest.py`

- `ingest_contexts(system, runtime, contexts, declarations)`: crea `Context`, `Symbol`, relación y
  `WiGame(ctx, R)` por S-expr (`create context …`, `create wigame …`, `assert …`). Es aditivo: se puede
  llamar por lotes sobre el mismo `system`.
- `build_world(corpus_dir, unit, lang, backend, limit, batch_size=40)` → mundo completo con
  `converge_in_batches`.

### 5.5 `pipeline/convergence.py`

**`context_taxonomy(system, contexts, declarations, min_support=2, max_features=600)`**
Matriz contextos × rasgos (`sign:<norm>` de signos `name`/`term` y `config:<R>:<norm(b)>`).
`phi_entropic` → `cohesion_pair` → `build_hierarchy` → `significant_levels`. Nodos = clases
significativas ∪ clases maximales. `nests` = aristas `ctx_A → ctx_B` con φ ≥ 0.9. `max_features`
limita a los rasgos más frecuentes porque `build_hierarchy` es O(p²) por nivel en Python.

**`symbol_convergence(system, contexts, declarations, phi_min=0.90, min_support=2,
min_contexts=2, max_iter=5, measure=phi_classical_pairs, taut_df=0.30, report=None,
max_config_size=500)`**

1. Variables: ocurrencias con ≥ `min_support` declaraciones.
2. `_configurations`: índice `configuración → {ocurrencias}`. Descarta las declaradas en menos de
   `min_contexts` contextos y las que aparecen en más de `taut_df` de los contextos (se registran en
   `tautological_configurations`).
3. `_candidate_pairs`: pares ordenados que comparten ≥ 1 configuración, por índice invertido;
   `n_st` = configuraciones compartidas; se puntúan los de `n_st ≥ min_support`. Una configuración con
   más de `max_config_size` ocurrencias no genera pares.
4. `contingency_pairs` + `phi_classical_pairs` sobre arreglos 1-D (Poisson exacta si λ ≤ 4, normal si
   no; `λ = n_a·n_¬b/n`).
5. Para cada par con φ ≥ `phi_min`, en orden `(−φ, s, t)`: si el inverso también ≥ `phi_min`, propuesta
   `equivalent`; si no, propuesta `projection` `s → t` por cada relación común, solo entre contextos
   distintos. Se promueve sin revisión cuando φ ≥ 0.95 (`PROMOTE_PHI`; en ambos sentidos para
   `equivalent`), `n_st ≥ 2` y las compartidas vienen de ≥ 2 contextos (dentro de un mismo contexto
   basta `n_st ≥ 2`). El resto queda en `proposed`.
6. Los `equivalent` promovidos reciben `ref:k`; la pasada siguiente recalcula las configuraciones con
   `ref(·)`. Termina cuando no hay promociones o en `max_iter`. Una segunda corrida no promueve nada.

`report.scores[s]` = mayor φ entrante desde otro contexto. `report.candidate_scores` = todos los
candidatos con su φ. `Symbol.metadata` guarda `convergence_score`, `contexts_supporting`, `referent`.
Los grupos viven en `system.referents` / `system.equivalences`.

**`converge_in_batches(system, contexts, declarations, batch_size=40, **kw)`**
Ordena contextos por documento y sección, acumula por lote y llama a `symbol_convergence`
arrastrando el `report` (referentes, puntajes, pares ya procesados). Cada lote vuelve a puntuar la
lista acumulada de candidatos y omite los ya procesados.

**`maintain_wigame(system, wigame_id)`**
Columnas tautológicas de `V_i` → `gates`. Colisiones de `ViMatrix.collapse_similarity()` →
`discriminants`: primera coordenada, en el orden de la jerarquía de `sia` sobre sujetos ×
coordenadas, presente en exactamente uno de los dos sujetos; si no hay, `unresolved`.

### 5.6 `pipeline/query.py`

`ask(system, relation, subject_symbol, object_norm=None, hops=2)` → `Answer`. Parte del juego
`wigame:<ctx>:<relation>` del sujeto, expande por el grupo de referentes y por las proyecciones
promovidas (en el sentido en que existen) hasta `hops`, y devuelve objetos, ruta de juegos y la cita
(`archivo:inicio-fin`) de cada hecho. `referent_of(system, symbol_id)`.

### 5.7 `pipeline/curate.py`

`select_candidates`, `propose`, `curate_queue`: arma para cada propuesta `projection`/`equivalent` un
prompt con las configuraciones compartidas y las oraciones citadas, y registra la respuesta del
backend (`keep`, `sexpr`, `comment`). No está conectado a la evaluación.

### 5.8 `sia/`

`contingency`, `contingency_pairs` (por bloques de 200 000 pares), `q_index`, `phi_classical`,
`phi_entropic` (α = 2), sus versiones `_pairs`, `confidence`, `cohesion_pair`, `cohesion_rrule`,
`build_hierarchy`, `significant_levels`, grafo implicativo y cierre, similitud de Lerman, AROMA.
Verificado contra la Tabla 1 del libro de SIA (τ = 0.6035, φ = 0.777, tolerancia 1e-3). La versión
por pares coincide con la densa con tolerancia 1e-9.

### 5.9 Runtime S-expr (`../src/`)

Verbos: `check`, `assert`, `ingest`, `create (symbol|relation|li|wigame|context)`, `candidate`,
`promote`, `reject`, `retract`, `why`, `define`, `project`, `return`. Verdad: `TRUE`, `FALSE`,
`UNKNOWN`.

## 6. Parámetros

| Parámetro | Valor | Efecto |
|---|---|---|
| `min_support` | 2 | declaraciones mínimas para ser variable; configuraciones compartidas mínimas para puntuar un par |
| `min_contexts` | 2 | contextos que deben declarar una configuración para que cuente |
| `taut_df` | 0.30 | fracción de contextos sobre la cual una configuración se descarta |
| `phi_min` | 0.90 | umbral de propuesta |
| `PROMOTE_PHI` | 0.95 | umbral de promoción sin revisión |
| `max_config_size` | 500 | tamaño máximo de una configuración que genera pares |
| `max_iter` | 5 | pasadas |
| `batch_size` | 40 | contextos por lote |
| `max_features` | 600 | rasgos de la jerarquía de contextos |

Cota útil: con inclusión perfecta φ = 1 − e^(−λ) si λ ≤ 4 y Φ(√λ) si no, con λ ≈ número de
configuraciones de la ocurrencia. Valores: 1 → 0.632, 2 → 0.865, 3 → 0.950, 4 → 0.982, 5 → 0.987.
Un par con menos de 3 configuraciones compartidas no puede llegar a `phi_min`.

## 7. Ejecución

Toda corrida que pueda pasar de 2 GB va con tope de memoria, una por comando:

```bash
bash scripts/capped.sh <GB> -- <comando>
```

`capped.sh` usa `systemd-run --user --scope -p MemoryMax=<GB>G -p MemorySwapMax=0`; si no hay
`systemd-run`, `ulimit -v`. Exit 137 = muerto por el tope. Reglas para workers en
`.herdr/briefs/_reglas.md`.

```bash
# mundo y propuestas
python -m pipeline.ingest      corpus/physicists/articles --lang en [--unit section] [--limit N]
python -m pipeline.convergence corpus/physicists/articles --lang en [--unit section] [--limit N]

# caché de declaraciones LLM (requiere pi + deepseek-flash; una vez)
python -m pipeline.decompose_batch corpus/physicists --regime pairs --backend pi --workers 8

# evaluación
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists \
    --regime {document,section,pairs} --decomposer {heuristic,llm,both} \
    [--source {simple,en}] [--with-sections] [--taxonomy] [--max-memory-gb 4] --out <dir>

bash scripts/capped.sh 4 -- python -m experiments.eval_matrix_kb <kb_dir> \
    [--min-contexts N] [--taut-df F] --out <dir>

# REPL
cd .. && PYTHONPATH=matrix-shrdlu-spec python -m desk.drawer.shrdlu.repl matrix-shrdlu-spec/corpus/physicists/en --lang en

# tests
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/
( cd .. && PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider )
```

Cada evaluación escribe `metrics.json` (parcial tras cada etapa) y `report.md` en `--out`.

## 8. Corpus

`corpus/physicists/` (generado por `python -m corpus.physicists.build`; `--english-only` para
regenerar solo `en/`):

| Archivo | Contenido |
|---|---|
| `people.csv` | 89 personas: qid, etiqueta, `en_title`. SPARQL `P106/P279* Q169470`, nacidos 1850-1900, con artículo en Simple English; se excluyen 14 esbozos < 300 caracteres (`excluded.csv`) |
| `articles/<qid>.md` | Simple English Wikipedia; un extracto por petición (`exlimit=1`) |
| `en/<qid>.md` | Wikipedia en inglés con secciones `## `; corta en *See also/References/…*; máx. 40 000 caracteres en límite de sección; 1.8 MB |
| `facts.jsonl` | 2 802 hechos de Wikidata sobre 12 relaciones |
| `mentions.json` | menciones cruzadas entre artículos (60 artículos con alguna) |
| `gap-validation.tsv` | 454 filas de GAP (908 pares); `gap_in_corpus.tsv` tiene 0 filas |
| `declarations_llm.jsonl` | caché LLM: 178 chunks, 11 242 declaraciones, 2.0 MB |

Licencias: CC BY-SA (Wikipedia), CC0 (Wikidata). `tests/fixtures/curie_franklin.py`: 15 + 15
artículos sintéticos con 10 hechos falsos plantados. `corpus/vegetales/`: ejemplo lechuga/espinaca.

`eval_matrix_kb` lee, sin copiar ni modificar, una KB del repo original de Matrix:
`proposals/*.jsonl` (`context`, `relation`, `subject`, `object`, `subject_sign`, `object_sign`,
`provenance[].sentence`) y `aliases.yaml` (`{context, symbol, canonical}`).

## 9. Evaluación

### 9.1 Regímenes de `eval_physicists`

| Régimen | Contextos |
|---|---|
| `document` (`--source simple` / `en`) | 89, uno por persona |
| `section` (`--source en`) | 564 secciones |
| `pairs` | 178: artículo Simple + encabezado EN de la misma persona (`--with-sections` añade el resto) |

### 9.2 Métricas

| Clave en `metrics.json` | Definición |
|---|---|
| `pairs` | fracción de personas con alguna ocurrencia sujeto de Simple (`she`/`he`/etiqueta) vinculada (referente compartido o proyección promovida) a una del encabezado EN del mismo qid; desglose por tipo de par; `failures` con configuraciones de cada lado |
| `intra_context` | fracción de contextos donde el pronombre se vincula con la etiqueta |
| `ranking` | posición del correcto entre los candidatos de cada consulta, ordenados por φ; MRR, hit@1, hit@3 sobre todas las consultas; `unranked` = sin candidato |
| `false_merges` | promociones entre qids distintos sin mención cruzada |
| `qa`, `qa_pronoun_subject`, `qa_pairs` | cobertura y precisión de `ask` contra `facts.jsonl`, por etiqueta, por pronombre y con salto Simple → EN |
| `garbage` | fracción de 50 ocurrencias plantadas que queda aislada vs 50 reales |
| `world`, `timings` | conteos, `candidate_pairs`, `batches`, tiempos por etapa, `peak_memory_mb` |

### 9.3 Resultados medidos

Sintético (`tests/test_convergence.py`, `taut_df=1.0`): jerarquía de contextos con 5 nodos y pureza
100 %; `she@curie_i` agrupado con `marie_curie@`/`curie@` en 15/15; ningún `she@franklin` con
ocurrencias de Curie; 10/10 plantados aislados con puntaje 0.0; segunda corrida sin promociones.

`pairs`, 178 contextos:

| | heuristic | llm | both |
|---|---|---|---|
| declaraciones | 2 931 | 11 242 | 13 574 |
| ocurrencias / variables | 4 120 / 690 | 10 703 / 4 427 | 12 277 / 5 701 |
| pares candidatos | 37 | 275 | 326 |
| declaraciones por ocurrencia (media / mediana) | 1.42 / 1 | 2.10 / 1 | 2.21 / 1 |
| `pairs` | 1/77 | 5/79 | 8/81 |
| `intra_context` | 0/157 | 0/158 | 0/161 |
| MRR / hit@1 / hit@3 | 0.055 / 0.043 / 0.053 | 0.265 / 0.250 / 0.261 | 0.243 / 0.219 / 0.250 |
| consultas con candidato | 13/94 | 34/92 | 38/96 |
| `false_merges` | 0 | 0 | 1 |
| QA cobertura etiqueta / con salto | 0.002 / 0.0 | 0.011 / 0.048 | 0.012 / 0.045 |
| QA precisión | 1.0 | 1.0 | 1.0 |
| basura aislada plantada / real | 1.0 / 0.98 | 1.0 / 0.96 | 1.0 / 0.92 |
| promovidos / propuestos / referentes | 6 / 65 / 3 | 45 / 296 / 18 | 98 / 352 / 42 |
| pico / tiempo | 198 MB / 2.5 s | 250 MB / 10.2 s | 274 MB / 14.4 s |

Otros regímenes (heurística): `document` Simple 0 promociones; `document` EN 4–7 proyecciones;
`section` EN 3 promociones, vínculo intra-artículo 0.0 y una fusión falsa
(`it@Q153238#1 ~ it@Q9123#5`, φ = 0.9626). GAP: cobertura 0.

`eval_matrix_kb` sobre `Matrix/examples/kb_wikipedia_10_articles` (699 propuestas, 10 contextos, 70
pares de alias en `aliases.yaml`):

| | `min_contexts=2, taut_df=0.30` | `min_contexts=1` | `min_contexts=1, taut_df=1.0` |
|---|---|---|---|
| configuraciones crudas → tras filtros | 1 118 → 20 | → 404 | → 407 |
| pares candidatos | 70 | 94 | 178 |
| candidatos con φ ≥ 0.90 | 0 | 0 | 0 |
| pares de alias propuestos / fusiones falsas | 0 / 0 | 0 / 0 | 0 / 0 |
| MRR / hit@1 / hit@3 | 0.089 / 0.049 / 0.146 | 0.146 / 0.122 / 0.195 | 0.158 / 0.122 / 0.171 |
| consultas con candidato (de 41) | 6 | 8 | 11 |
| φ máx. de un par de alias / de cualquier candidato | 0.573 / 0.817 | 0.783 / 0.863 | 0.781 / 0.863 |

Pares de alias por configuraciones compartidas (sin filtros): 60 con 0, 8 con 1, 2 con 2, ninguno
con ≥ 3. 44 de los 70 incluyen una ocurrencia con una sola declaración. Detalle en
`.herdr/matrix_kb_report.md`.

### 9.4 Memoria antes y después del rediseño por pares candidatos

| Descompositor | Variables | Pico antes | Pico ahora | Tiempo antes | Tiempo ahora |
|---|---|---|---|---|---|
| heuristic | 690 | 1 488 MB | 198 MB | 4.7 s | 2.5 s |
| llm | 4 427 | 7 921 MB | 250 MB | 245 s | 10.2 s |
| both | 5 701 | OOM a 11 GB | 274 MB | — | 14.4 s |

Causa del OOM (commit anterior a `28cd050`): contingencia, puntajes y `n_st` densos p×p, más las
matrices temporales de `phi_classical`, un diccionario por cada par y bucles Python O(p²);
`_ranking_metrics` recalculaba la matriz entera. Test de escala: 3 000 ocurrencias en 300 contextos,
16 MB y 3.2 s.

## 10. Limitaciones conocidas

- Un nodo por `signo@ctx`: si un signo cambia de referente dentro de un contexto, el código no lo
  distingue.
- `min_contexts=2` descarta toda configuración declarada en un solo contexto, así que no puede haber
  propuestas entre ocurrencias del mismo contexto cuando hay un contexto por documento.
- `taut_df` es una fracción de contextos: con un solo contexto descarta todas las configuraciones.
- La promoción sin revisión está activa por defecto; no hay flag para dejar todo en `proposed`.
- El circuito con un intérprete (LLM o persona) decidiendo sobre las propuestas no está implementado
  ni medido; `curate.py` existe pero no está en la evaluación.
- `context_taxonomy` solo se evaluó en el sintético; en el corpus real es opcional (`--taxonomy`) y
  está limitada a 600 rasgos.
- `converge_in_batches` vuelve a puntuar la lista acumulada de candidatos en cada lote.
- Los objetos no se canonicalizan: `Nobel Prize` y `Nobel Prize in Chemistry` producen
  configuraciones distintas.
- Una enumeración en una sola oración aporta una configuración por elemento (p. ej. las 9
  `field|a|<disciplina>` que vinculan `bose@Q45789` con `he@Q45789#0`).
- `/tmp/eval` no persiste; las cifras están en `.herdr/*_report.md` y se regeneran con §7.

## 11. Historial relevante

| Commit | Cambio |
|---|---|
| `fff87d5` | `specs/convergence.md` |
| `ecabc8e`, `b4c6f2f` | contextos con signos locales; descomposición e ingesta por contexto |
| `83a866f` | jerarquía de contextos, vínculos entre ocurrencias, mantenimiento |
| `97969f4` | corpus de físicos |
| `2f8a41a` | `ask` y evaluación |
| `cc12bb0`, `d30570a` | regímenes `section` y `pairs`; filtro de tautología; guarda `n_st ≥ 2` |
| `28cd050` | pares candidatos, lotes, `capped.sh` |
| `8ebd7c2` | descompositor LLM cacheado; ranking sobre todos los candidatos |
| `da21ea3` | retiro del puente por co-ocurrencia; specs y README alineados |
| `9c2dc53` | `eval_matrix_kb` |

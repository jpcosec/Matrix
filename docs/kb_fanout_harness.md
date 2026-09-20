# KB Fan-out Harness (Materialized View)

Operational record of the harness that populates the Matrix KB from real text, and
of the measurements taken when scaling contexts/WiGames. Materialization of the
atom `Aplicaciones/KB_Fanout_y_Stress_de_Contextos.md`.

## Pipeline

```bash
python -m tools.kb --kb kb fetch "Marie Curie"
python -m tools.kb --kb kb prepare --max-chars 2500
# subagentes libres: 1 worker por prompt -> kb/candidates/<slug>/<idx>.jsonl
python -m tools.kb --kb kb ingest --min-confidence 0.0
python -m tools.kb --kb kb review render
python -m tools.kb --kb kb review all --decision approved --relation premio --reviewer jp
python -m tools.kb --kb kb compile
python -m tools.kb --kb kb verify --fail-on-problems
```

Roles:

- **Subagentes** (cualquier modelo barato; acá `pi` + `deepseek-flash`) sólo leen un chunk y escriben JSONL de candidatos.
- **`ingest`** valida determinísticamente y emite **propuestas `pending`** context-scoped. No toca la KB.
- **Review gate** (`kb/review.yaml`): `approved` / `rejected` con reviewer, nota y fecha.
- **`compile`** materializa sólo aprobadas: `wigame:<contexto>:<relación>` con `context_id`, árbol `contexts.yaml`, `aliases.yaml` y `projections/*.yaml`.
- **`verify`** re-chequea cada hecho por `SExpressionRuntime` y valida `context_id`, contextos y proyecciones.

## Modelo de contexto

Un `WiGame` es **(ejes + relación) bajo un contexto**. Por eso:

- el `contexto` es parte de la identidad (`wigame:<ctx>:<rel>`), no metadata;
- el mismo `(R a b)` en dos artículos son dos hechos, no uno;
- la identidad entre contextos es curación revisada (`kb/aliases.yaml`), materializada como `RoutingProjection`;
- los contextos forman un árbol: `ctx:kb` → `ctx:<fuente>` → hojas WiGame.

Ver [WiGame, Context and Disambiguation](./context_and_wigame.md).

## Layout

```
kb/
  sources/ work/ candidates/      # fuente, chunks, salida de subagentes
  proposals/ review.yaml review_pending.md
  aliases.yaml                    # curación (contexto, símbolo) -> referente
  facts/ symbols.yaml relations.yaml contexts.yaml projections/
  wigames/                        # KB compilada
  manifest.yaml *_report.json
```

## Gates

| Gate | Comando | Criterio |
|---|---|---|
| Contrato | `ingest` | `unparseable`/`rejected` con motivo |
| Contexto | `contexts` | 1 contexto por fuente; WiGames con `context_id` |
| Revisión | `review summary` | nada `pending` se cuela (`excluded.pending`) |
| Identidad | `aliases.yaml` + `projections/` | alias revisados; proyecciones sólo por referente compartido |
| Reproducible | `verify --fail-on-problems` | `ok: true`, `problems: []` |

## Contrato ejecutable

`tests/test_kb_fanout.py` verifica: propuestas context-scoped y `pending`,
`compile` sólo con aprobadas, `context_id` y árbol de contextos, alias +
proyección cross-contexto, y el bloqueo de `pending`.

## Stress-test

```bash
# sintético
python -m tools.kb --kb kb stress --contexts 250 --relations 4 --own-refs 8 \
    --shared-refs 40 --contexts-per-shared-ref 8 --root kb/stress

# real (DBpedia: contexto = categoría, referente = persona, perfil = categorías)
python -m tools.kb --kb kb stress --mode wikipedia --source dbpedia \
    --category "20th-century women scientists" --limit 600 --max-contexts 200 \
    --attrs-per-member 2 --root kb/stress
```

### Mediciones

| | sintético (250 ctx, 4640 facts, 995 WiGames) | real (172 personas, 200 ctx, 1498 facts) |
|---|---|---|
| ingest / compile / verify | 0.5s / 6.4s / 7.3s | 0.27s / 4.1s / 5.6s |
| `load_system` (cold) | 7.0s | 5.8s |
| ruteo hot p50 / p95 | 0.012ms / 0.016ms | 0.010ms / 0.064ms |
| ruteo cold | ~7.1s | ~5.5s |
| proyecciones | 2000 (cap) | 2000 (cap) |
| RSS / disco | 96MB / 13MB | 66MB / 8.4MB |
| curva desambiguación | k=1: 52% → k=2: 91% → k=4: 100% | k=1: 83% → k=2: 100% |

### Lectura

- La desambiguación por acumulación de contextos se sostiene con datos reales y sin curación previa.
- El cuello de botella es la hidratación total (cold ≈ `load_system`) y la generación O(contextos²) de pares de proyección; el ruteo en caliente es trivial.
- `compile --max-projection-pairs` (default 2000) reporta `projections_truncated`.
- Wikipedia API rate-limita bajo ráfaga (429); DBpedia resuelve el corpus real en una query SPARQL cacheada.

## Corpus de software (contexto = módulo)

La misma pipeline corre sobre un repo de software, con extracción **determinística por AST** (sin LLM):

```bash
python -m tools.kb --kb kb software --path src/operational_model --path tests --base .
python -m tools.kb --kb kb ingest
python -m tools.kb --kb kb review all --decision approved --reviewer ast
python -m tools.kb --kb kb compile && python -m tools.kb --kb kb verify --fail-on-problems
```

Mapeo: **contexto = módulo**, **referente = símbolo**; relaciones `define_en (símbolo, class|def)`, `usa (receptor, miembro)`, `importa (nombre, import)`, `hereda_de (clase, base)`. Cada `sentence` es la línea de código exacta, así que el contrato del harness (verbatim + sujeto/objeto presentes) se cumple por construcción (0 rechazos).

Corrida sobre este repo (`src/operational_model` + `tests`, 86 módulos):

| métrica | valor |
|---|---|
| contextos / WiGames | 86 / 211 |
| facts / rechazos | 1494 / 0 |
| proyecciones | 1736 (`define_en` 82, `importa` 838, `usa` 816) |
| imports externos descartados | 163 (`--all-imports` los conserva) |
| capabilities | 26/26 |

Ruteo cross-contexto real (dependencias compartidas): desde `...vi_matrix:importa` con `import` se proyecta a `si_matrix` y se intersecta:

```json
{"source_hits": ["booleanmatrix", "new_id", "searchvector", "truthvalue"],
 "projected_hits": ["booleanmatrix", "new_id"],
 "cross_hits": ["booleanmatrix", "new_id"]}
```

Hallazgo: el problema de homónimos también existe en código. `post_init` está definido en 4 contextos distintos (`core_relation`, `core_thing`, `matrices_boolean_matrix`, `system_wigame`): misma superficie, referentes distintos. Igual `self`/`cls`/`payload` en `usa` generan proyecciones de falsos amigos. `internal_only` (default) filtra imports de stdlib, que inflarían el espacio de proyecciones.

## Máquinas, recetas y operatoria

Contenido secuencial (instrucciones) necesita una capa más: la **operatoria** de dominio, que declara cómo se lee el texto como máquina. Ver [Operatoria: cómo leer una receta](./operatoria_recetas.md).

```bash
python -m tools.kb --kb kb machine             # operatoria + specs -> candidatos
python -m tools.kb --kb kb ingest && python -m tools.kb --kb kb review all --decision approved --reviewer operatoria
python -m tools.kb --kb kb compile             # aplica el álgebra declarada (cierre transitivo)
python -m tools.kb --kb kb reachability        # cierre vs oráculo BFS, ciclos, inalcanzables, equivalencias
python -m tools.kb --kb kb shared --symbol cebolla
```

- Specs autoradas: `tools/kb/operatoria/*.yaml` (relaciones, álgebra, operaciones, errores) y `tools/kb/machines/*.yaml` (FSM y recetas).
- La operatoria se materializa como contexto propio: `ctx:operatoria` → `wigame:operatoria:declara` (la spec es consultable).
- `compile` aplica el álgebra: `precede`/`sustituye_a` transitivos ⇒ hechos derivados (`facts_derived.jsonl`, `derived_facts` en el manifest); `paralelo_con` conmutativo ⇒ simetrización.
- `shared.yaml` registra símbolos compartidos por ≥2 contextos **en cualquiera de los dos ejes** (los ingredientes viven en el eje de objetos, y `RoutingProjection` sólo proyecta sujetos).

Corrida de referencia (5 contextos: `trafico`, `ascensor`, `ragout`, `bechamel`, `guiso` + `operatoria`):

| métrica | valor |
|---|---|
| facts / derivados | 103 / 34 |
| WiGames / contextos | 20 / 7 |
| recetas | `ragout`, `guiso`, `bechamel`: acíclicas, cierre derivado |
| FSM | `trafico`: ciclo esperado, `verde_peatonal` inalcanzable y equivalente a `verde` |
| oráculo | cierre vs BFS: **acuerdo total** en los 5 contextos |
| sustituciones | `(sustituye_a manteca margarina)` = `true` (derivado) |
| compartidos | `cebolla`/`vino`/`caldo` (guiso↔ragout), `manteca` (bechamel↔ragout) |

## Ejemplos guardados

Catálogo reproducible en [`examples/README.md`](../examples/README.md): demo ejecutable del ragout, specs, digests de las cuatro KBs (máquinas, software, 10 artículos, Marie Curie) y `examples/regenerate.sh`.

## Capacidades verificadas (`capabilities`)

```bash
python -m tools.kb --kb kb capabilities    # escribe capabilities_report.json
```

Batería de 26 chequeos: **26 passed**. Grupos y hallazgos:

| grupo | qué verifica |
|---|---|
| `upserts` (5) | alta de fact, duplicado idempotente, `assert` sobre celda `false` → reject `widerspruechlich`, `ingest` registra sin verdad (`Vi=∅`), `set_sense` override |
| `inference` (4) | conmutativa (`bRa` inferido), clausura transitiva (`aRc` inferida), sin álgebra no hay inferencia, y **`WiGame.add_fact` no aplica álgebra** (sólo `LogicalSystem.add_fact`) |
| `queries` (7) | `SearchVector` local, `check` verdad/`reject` fuera de `Li`, `get_status` (`sinnvoll`/`unsinnig`), `cross_search`, `route_search` multi-hop |
| `sense` (3) | `is_pure`, columnas tautológicas, `information_energy` |
| `serialization` (1) | roundtrip `to_yaml`/`from_yaml` de `WiGame` |
| `kernel` (2) | `parse_formula` + `collect_atoms` + `evaluate_formula` |
| `kb` (4) | todo WiGame tiene `context_id`, pronombres resueltos, proyecciones cross-contexto, árbol con raíz |

Gaps registrados:

- `search` con un término inexistente lanza `KeyError` explícito; no distingue "término inválido" de "sin resultados".
- `compile` no aplica inferencia: los WiGames se arman con `WiGame.add_fact`, que evita la clausura transitiva (a propósito: evita O(n³) por hecho).
- La extracción deja objetos como `her_parents` / `hahn_and_strassmann` (referentes colectivos); la curación por alias sólo cubre símbolos simples.

## Notas de estado

- Fix en `src/operational_model/system/s_expression_runtime.py`: `(check|assert wigame:<inexistente> ...)` devolvía `KeyError`; ahora devuelve `reject: target WiGame does not exist` (+ test de regresión).
- Recuperados los 5 errores de colección pre-existentes: `tests/test_shrdlu_*` importaban `prototypes.shrdlu` (paquete movido a `desk/drawer/shrdlu`) y `tests/test_ragout_demonstration.py` importaba `examples/`, que estaba purgado. El demo del ragout se reconstruyó en `examples/ragout_demonstration.py`.
- Suite completa: **133 passed, 0 collection errors**.
- Sin commits. Nuevos: `.pi/`, `tools/`, `examples/`, `docs/context_and_wigame.md`, `docs/kb_fanout_harness.md`, `docs/operatoria_recetas.md`, `tests/test_kb_fanout.py`, `tests/test_kb_machine.py`.

## Relacionado

- Skill de uso: `.pi/skills/matrix-kb-fanout/SKILL.md`
- Átomos: `WiGame_Contexto_y_Desambiguacion`, `WiGame`, `Contexto_Logico`, `Juego_de_Desambiguacion`, `Colapso_Dimensional`

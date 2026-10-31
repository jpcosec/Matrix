# Matrix — el motor booleano

El motor vive en `../src/` de este repo; antes era un subtree en `matrix/` (commit `38dcfbd`), traído con historial y arreglado para que su suite pase (179 tests). Se modifica libremente; su antiguo SSOT de átomos no es vinculante. Esta página dice qué se usa, qué se cambia y qué se ignora.

## 1. Lo que se usa tal cual

| Pieza | Archivo | Qué hace |
|---|---|---|
| `Fact`, `Proposition`, `TruthValue`, `SenseValue` | `src/operational_model/core/{fact,proposition,truth_value,sense_value}.py` | Unidad lógica `(R a b)` con verdad `TRUE/FALSE/UNKNOWN`, sentido `sinnvoll/sinnlos/unsinnig` y `evidence: dict`. |
| `Symbol`, `Name`, `Thing`, `Relation`, `LiSpace` | `core/{symbol,name,thing,relation,li_space}.py` | Catálogo de símbolos con signos, relaciones con álgebra (`commutative/transitive/…`), ejes admisibles `axis_a × axis_b`. |
| `WiGame` | `system/wigame.py:19` | Mundo local con su `Vi`, `Si`, hechos y proposiciones; `accepts/add_fact/search/is_pure/…`. |
| `BooleanMatrix`, `ViMatrix`, `SiMatrix` | `matrices/` | Matrices con ejes nombrados; `bool_mult` por bitmasks; `transitive_closure` reflexivo-transitiva por *squaring* (`boolean_matrix.py:178`). |
| `RuleMatrixCompiler`, `modus_ponens`, `hypothetical_syllogism` | `kernel/rule_matrix.py:25`, `kernel/formula_inference.py` | `(if a b)` → Implication Matrix `I`; deducción `v ⊗ I*`. |
| `RoutingProjection`, `Context`, `SearchVector` | `routing/` | Proyección `entidad × entidad` entre dos `WiGame`; `project_subjects`, `bool_mult`. |
| `SExpressionRuntime` | `system/s_expression_runtime.py:32` | Verbos `check / assert / ingest / create / return` → `OperationResult(status, sinn, payload, reason)`. |
| Serialización YAML de mundos | `system/wi_game_serialization.py`, `examples/*.yaml` | Formato `wigame_id, axis_a, axis_b, relation, Vi{1/0/∅}, Si{V/L/U}, facts[]`. |
| Prototipo SHRDLU | `../desk/drawer/shrdlu/` | Léxico, parser de inglés controlado → frames, `DialogState`, lowering a S-expr. |

## 2. Lo que se cambia

| Cambio | Motivo | Doc |
|---|---|---|
| Esquema de `Fact.evidence` (`prov`, `tier`, `curation`, `stats`, `derived_from`, `history`) y validación en `add_fact` | hoy es un dict libre que nadie lee | [provenance.md](provenance.md) |
| `assert` acepta `evidence`; `UNKNOWN` no alimenta `v` en `modus_ponens` | separar propuesto de confirmado | [provenance.md](provenance.md) |
| Verbos nuevos `retract`, `promote`, `reject`, `why`, `define`, `return candidates` | curado y loop de interacción | [runtime_api.md](runtime_api.md) |
| `DialogState` real (pila de referentes, foco, aclaración) | hoy solo resuelve `it/them/they` al último referente | [shrdlu.md](shrdlu.md) |
| Ingesta por contexto (`pipeline/ingest.py`): un `WiGame` por `(contexto, relación)` con sus símbolos, `li` y las declaraciones como hechos `observed` | la unidad es el juego de lenguaje, no la oración | [convergence.md](convergence.md) §4 |
| Proyecciones y equivalencias pobladas por la convergencia (`pipeline/convergence.py`), no por SIA directo | la identidad entre contextos se propone por convergencia y se confirma por curado | [chic.md](chic.md) §5 |

## 3. Lo que se ignora

- `desk/`, `Whitepaper/`, `docs/*.md` "atomizados" (`proposition_first_architecture.md`, `data_models.md`): vistas de un SSOT que ya no gobierna. Se podan cuando estorben.
- Hipertensor canónico global y migración a JAX (`desk/pills/pill-migracion-a-jax.md`, tareas `[draft]`): no se hacen. El estado vive en cada `WiGame`.
- `language/owl2matrix.py`: se mantiene por si sirve de importador, sin desarrollo.

## 4. Convenciones heredadas

- Forma canónica externa `(R a b)`; interna en campos separados (`relation_id, subject_symbol_id, object_symbol_id`).
- Tests: `pytest` desde la raíz del repo, imports `from src.operational_model...`, builders (`build_system()`) en vez de fixtures, un archivo por módulo.
- Cuando `(R a b)` cabe en más de un `WiGame`, el runtime devuelve `status="ambiguous"` con `payload.candidates`; nunca elige en silencio.
- **Nunca `p×p`**: ninguna estructura puede crecer con el cuadrado del número de símbolos del corpus
  (tres OOM el 2026-09-20). La intensidad se calcula sobre la lista de pares candidatos
  (`sia.contingency.contingency_pairs`), con índice invertido configuración → símbolos; la
  convergencia entra por lotes (`converge_in_batches`). El límite de memoria por comando es de 4 GB
  (`scripts/capped.sh`).

# Matrix-SHRDLU — Especificación de producto

## 1. Qué es

Un motor de conocimiento que **puebla** mundos lógicos (`WiGame`) desde texto crudo y que se
**usa** conversando como con SHRDLU.

- **Poblar:** el `Populator` recorta el corpus en **contextos** (chunks) y extrae sus signos locales
  con offsets exactos; un **descompositor** (heurística o LLM barato) convierte cada oración en
  declaraciones `(R a b)` sobre esos signos; cada `(contexto, relación)` se materializa como un
  `WiGame` cuyos hechos son `observed` de ese juego. La **convergencia** (CHIC/SIA) propone qué
  símbolos de contextos distintos son el mismo referente (`equivalent`) y qué proyecciones
  (`projection`) los conectan; un humano confirma.
- **Usar:** el usuario afirma, pregunta, pide "¿por qué?", recibe preguntas de aclaración cuando un
  signo es ambiguo y define conceptos nuevos en caliente. Todo se evalúa con álgebra booleana sobre
  `S_i`, `V_i` e `I`, y las preguntas cruzan mundos por las proyecciones promovidas.

Flujo ([convergence.md](convergence.md) §4):

```
texto ─► Populator: chunks (contextos), signos locales, offsets
              │
              ▼
      descompositor por oración ─► declaraciones (R a b) @contexto, con Prov(f)
              │
              ▼
      runtime: WiGame(ctx, R) ─► sentido (indexación, contradicción) ─► V_i por contexto
              │
              ▼
      CHIC: contextos × rasgos      ─► árbol de contextos
            configuraciones × símbolos ─► proyecciones / equivalent
            sujetos × coordenadas (por W_i) ─► compuertas, subjuegos, D_i
              │
              ▼
      promoción por convergencia o curado ─► consultas ruteadas (ask, route_search) con Prov
```

## 2. Componentes y documentos

| Componente | Doc | Estado |
|---|---|---|
| Capa de signos (chunks, signos locales, offsets) | [populator.md](populator.md) | `populator/`; el chunk es la unidad |
| Descomposición e ingesta por contexto | [convergence.md](convergence.md) §4 | `pipeline/decompose.py`, `pipeline/ingest.py`; heurística + LLM (`decompose_llm_chunk`, `pipeline/decompose_batch.py`) |
| Convergencia (taxonomía, símbolos, mantenimiento) | [chic.md](chic.md), [convergence.md](convergence.md) §3 | `sia/` + `pipeline/convergence.py` (`converge_in_batches`) |
| Curado y anclaje a la fuente | [grounding.md](grounding.md), [provenance.md](provenance.md) | `core/evidence.py`, `system/candidates.py`, `system/deduction.py` |
| Motor booleano (WiGame, `S_i`, `V_i`, `I`, runtime S-expr) | [matrix.md](matrix.md) | `matrix/` (subtree de `jpcosec/Matrix`), 179 tests |
| Consultas ruteadas y REPL | [shrdlu.md](shrdlu.md), [runtime_api.md](runtime_api.md) | `pipeline/query.py`, `matrix/prototypes/shrdlu/{spanish,repl}.py` |
| Evaluación | [convergence.md](convergence.md) §7 | `experiments/eval_physicists.py`, `corpus/physicists/` |
| Causalidad | [appendix_causality.md](appendix_causality.md) | fuera de alcance |
| Fuentes | [sources.md](sources.md) | — |

## 3. Decisiones cerradas

| # | Tema | Decisión | Dónde está hoy |
|---|---|---|---|
| 1 | Dónde vive el estado | Cada `WiGame` tiene su `V_i`/`S_i`; los cruces entre mundos van por `RoutingProjection`. El "hipertensor global" de los átomos de Matrix nunca se implementó y queda como optimización futura. | `matrix/src/operational_model/system/wigame.py:19` |
| 2 | El símbolo | Es `(signo, contexto)`: `she@Q7186 ≠ she@Q937`. Sin plegado de alias; la normalización solo reconoce repeticiones dentro del chunk. La identidad la propone la convergencia. | `populator/contexts.py`, [convergence.md](convergence.md) §1 |
| 3 | Valores de verdad | Tres: `TRUE / FALSE / UNKNOWN(∅)`. `UNKNOWN` es el estado de todo lo propuesto y no curado. | `core/truth_value.py:8` |
| 4 | Sentido | Tres: `sinnvoll / sinnlos / unsinnig`. Las configuraciones verdaderas para casi todos los contextos se descartan (no discriminan). | `core/sense_value.py:8`, `pipeline/convergence.py` (`taut_df`) |
| 5 | Clausura e inferencia | Booleana: `I* = ⋁_k I^k` por *squaring* (`O(log N)` productos); modus ponens `v ⊗ I*`. Nunca suma aritmética de potencias. | `matrices/boolean_matrix.py:178`, `kernel/formula_inference.py:11` |
| 6 | Escala | **Nunca `p×p`**: la intensidad se calcula sobre la lista de pares candidatos (índice invertido configuración → símbolos) y la convergencia entra por lotes. Los mundos son aglomerativos: los contextos se comparan contra el mundo ya construido, no todos contra todos. | `sia/contingency.py::contingency_pairs`, `pipeline/convergence.py::converge_in_batches` |
| 7 | Backend numérico | NumPy + `scipy.sparse` para `sia/`; Python puro en `matrix/`. JAX no entra hasta que el vocabulario sea estable (los shapes dinámicos de `create symbol` lo penalizan). | — |
| 8 | Superficie de mando | S-expressions. Se conservan `check / assert / ingest / create / return`; se añaden `retract`, `promote`, `reject`, `why`, `define`, `project` y `create context`. | `system/s_expression_runtime.py:38` |
| 9 | Procedencia | En `Fact.evidence`: `Prov(f) = (document_id, span, extractor, confidence)` + `tier` + `curation`. No hay matrices de procedencia. | `core/fact.py:20` |
| 10 | Rol del LLM | Descompone superficie (una llamada por chunk) y verbaliza. No decide verdad, sentido ni identidad. | [shrdlu.md](shrdlu.md), [grounding.md](grounding.md) §3 |

## 4. Alcance implementado (pasos A-D, todos con tests)

1. **A — contextos y signos locales** (`populator/contexts.py`): `chunk_documents`, `build_context`,
   `LocalSign`, `SignIndex`; ventanas de nombre con conectores y pronombres preservados;
   `tests/test_contexts.py`.
2. **B — descomposición e ingesta** (`pipeline/decompose.py`, `pipeline/ingest.py`): declaraciones
   por oración (heurística por patrones + `decompose_llm_chunk` con `PiBackend` cacheado en
   `corpus/physicists/declarations_llm.jsonl`), un `WiGame` por `(contexto, relación)` y `assert`
   con `Prov(f)`; `tests/test_decompose.py`, `tests/test_ingest.py`,
   `tests/test_decompose_llm_chunk.py`.
3. **C — convergencia** (`pipeline/convergence.py`): taxonomía de contextos, convergencia de
   símbolos (`equivalent` / `projection`), mantenimiento de `W_i` (compuertas y `D_i`),
   `converge_in_batches`; `tests/test_convergence.py`, `tests/test_convergence_pairs.py`.
4. **D — consultas y evaluación** (`pipeline/query.py`, `experiments/eval_physicists.py`): `ask` con
   ruta y cita sobre proyecciones promovidas, REPL en español e inglés, y los regímenes
   `document` / `section` / `pairs` con los descompositores `heuristic` / `llm` / `both`;
   `tests/test_query.py`, `tests/test_eval_smoke.py`, `matrix/tests/test_shrdlu_*.py`.

Fuera del alcance: causalidad (requiere datos, no texto — apéndice) y backend JAX.

## 5. Ventajas que sí se sostienen

- **La KB mejora con volumen:** un hecho real converge desde muchos contextos; la basura no
  encuentra configuraciones compatibles en otros contextos y queda aislada. Medido: en
  `corpus/physicists`, el 100 % de los 50 hechos plantados queda aislado frente al 96 % de los
  hechos reales (y con el descompositor LLM el contraste es 1.0 vs 0.96).
- **Identidad por convergencia, no por string:** `equivalent` exige φ alto en ambos sentidos y ≥ 2
  configuraciones informativas compartidas; nunca se pliega un alias a la entrada.
- **Trazabilidad total:** ningún hecho entra sin cita; `why` devuelve la cadena de implicaciones y
  sus fuentes; `ask` devuelve la ruta y la cita.
- **Rechazo de absurdos:** `S_i` filtra proposiciones sin sentido antes de tocar `V_i`; el LLM no
  puede colar relaciones fuera de las familias.
- **Coste acotado:** toda la convergencia corre en memoria de cientos de MB (`< 300 MB` en los tres
  regímenes de evaluación) porque ninguna estructura crece con `p²`.

Resultados completos y diagnóstico en [convergence.md](convergence.md) §7.

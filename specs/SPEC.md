# Matrix-SHRDLU — Especificación de producto

## 1. Qué es

Un motor de conocimiento que **puebla** mundos lógicos (`WiGame`) desde texto crudo y que se **usa** conversando como con SHRDLU.

- **Poblar:** un chunker estadístico (fases 1-3 de Korel) convierte un corpus en una matriz binaria `individuos × conceptos`; CHIC (Análisis Estadístico Implicativo) descubre sobre ella símbolos, jerarquías e implicaciones `a → b` con su intensidad. Cada hallazgo lleva su cita de origen (`Prov(f)`), entra al motor como `UNKNOWN` y se confirma mediante curado (LLM propone, humano decide).
- **Usar:** el usuario afirma, pregunta, pide "¿por qué?", recibe preguntas de aclaración cuando hay ambigüedad y define conceptos nuevos en caliente. Todo se evalúa con álgebra booleana sobre las matrices de sentido (`S_i`), verdad (`V_i`) e implicación (`I`) que ya implementa Matrix.

```
texto ──► Populator (Korel f.1-3) ──► X: individuos×conceptos (+offsets)
                                              │
                                              ▼
                              sia/: ϕ, φ entrópica, cohesión, jerarquía, grafo
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                     ▼                     ▼
                  Symbol/Relation       jerarquía → C_k /       grafo implicativo →
                  catálogos + S_i       WiGame hijo + WC        Implication Matrix I
                        └──── cola de curado (LLM propone, humano confirma) ────┘
                                              │  cada hecho: Prov(f), tier, UNKNOWN→TRUE
                                              ▼
                        matrix/ runtime  (check / assert / ingest / create / return …)
                                              ▲
                        SHRDLU-loop (parser, diálogo, why, define, aclaración)
```

## 2. Componentes y documentos

| Componente | Doc | Estado |
|---|---|---|
| Motor booleano (WiGame, `S_i`, `V_i`, `I`, runtime S-expr) | [matrix.md](matrix.md) | existe en `matrix/` (subtree de `jpcosec/Matrix`), 119 tests |
| Chunker estadístico | [populator.md](populator.md) | por implementar |
| CHIC / SIA | [chic.md](chic.md) | núcleo en `sia/` |
| Curado y anclaje a la fuente | [grounding.md](grounding.md), [provenance.md](provenance.md) | por implementar sobre `Fact.evidence` |
| Loop de interacción | [shrdlu.md](shrdlu.md), [runtime_api.md](runtime_api.md) | prototipo en `matrix/prototypes/shrdlu/` |
| Causalidad | [appendix_causality.md](appendix_causality.md) | fuera de alcance |
| Fuentes | [sources.md](sources.md) | — |

## 3. Decisiones cerradas

| # | Tema | Decisión | Dónde está hoy |
|---|---|---|---|
| 1 | Dónde vive el estado | Cada `WiGame` tiene su `V_i`/`S_i`; los cruces entre mundos van por `RoutingProjection`. El "hipertensor global" de los átomos de Matrix nunca se implementó y queda como optimización futura. | `matrix/src/operational_model/system/wigame.py:19` |
| 2 | Valores de verdad | Tres: `TRUE / FALSE / UNKNOWN(∅)`. `UNKNOWN` es el estado de todo lo propuesto por CHIC y no curado. | `matrix/src/operational_model/core/truth_value.py:8` |
| 3 | Sentido | Tres: `sinnvoll / sinnlos / unsinnig`. | `core/sense_value.py:8` |
| 4 | Clausura e inferencia | Booleana: `I* = ⋁_k I^k` por *squaring* (`O(log N)` productos); modus ponens `v ⊗ I*`. Nunca suma aritmética de potencias. | `matrix/src/operational_model/matrices/boolean_matrix.py:178`, `kernel/formula_inference.py:11` |
| 5 | Backend numérico | NumPy + `scipy.sparse` para `sia/`; Python puro en `matrix/`. JAX no entra hasta que el vocabulario sea estable (los shapes dinámicos de `create symbol` lo penalizan). | — |
| 6 | Superficie de mando | S-expressions. Se conservan `check / assert / ingest / create / return`; se añaden `retract`, `promote`, `why`, `define`. | `system/s_expression_runtime.py:38` |
| 7 | Procedencia | En `Fact.evidence`: `Prov(f) = (document_id, span, confidence, extractor)` + `tier` + `curation`. No hay matrices de procedencia. | `core/fact.py:20` |
| 8 | Conflictos | Señal explícita, nunca sobrescritura silenciosa; tres políticas (one-hot, dimensión discriminativa, confianza). | [provenance.md](provenance.md) |
| 9 | Complejidad | Se habla de paralelismo bitwise, no de `O(1)`. | — |
| 10 | Rol del LLM | Parsea y verbaliza. No decide verdad ni sentido. | [shrdlu.md](shrdlu.md) |

## 4. Alcance del MVP

1. `sia/`: intensidad clásica y entrópica, cohesión, jerarquía con niveles significativos, grafo implicativo. Tests contra la Tabla 1 y la Fig. 1 del libro.
2. Populator: Korel fases 1-3 sobre un corpus pequeño del dominio culinario/vegetal (`matrix/examples/vegetales*.yaml` como vocabulario semilla).
3. Puente `sia/report` → S-expressions (`create symbol/relation/li/wigame`, `ingest`) con `Prov(f)` en `evidence`, `tier=statistical`, `truth=UNKNOWN`.
4. Cola de curado + verbo `promote`.
5. SHRDLU-loop v1: REPL con `assert / check / why / define` y aclaración por ambigüedad.

Fuera del MVP: AROMA (proyecciones entre mundos), R-reglas de grado > 1, árbol de similitud, JAX, verbalización con LLM, causalidad.

## 5. Ventajas que sí se sostienen

- **Trazabilidad total:** ningún hecho entra sin cita; "¿por qué?" devuelve la cadena de implicaciones y sus fuentes.
- **Rechazo de absurdos:** `S_i` filtra proposiciones sin sentido antes de tocar `V_i`; el LLM no puede colar relaciones inexistentes.
- **Asimetría estadística:** CHIC distingue `a → b` de `b → a`; PMI y co-ocurrencia no.
- **Escalado por bits:** las operaciones sobre `I` y `V_i` son productos booleanos empaquetables; el coste crece con `log N` en profundidad, no con la longitud de la cadena deductiva.

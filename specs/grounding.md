# Grounding y curado

## 1. Principio

No se promete un mapeo automático texto → ontología. Lo que se garantiza es más modesto y verificable: **todo hecho de la base de conocimiento puede referenciarse a su fuente**, y nada pasa de `UNKNOWN` a `TRUE` sin una decisión registrada. El curado se automatiza al máximo, pero el paso final lo dan un LLM que propone y un humano que confirma.

## 2. Candidatos

`sia/report.py` produce cuatro tipos de candidato, cada uno con `Prov(f)` (ver [provenance.md](provenance.md)) y sus estadísticos:

| Tipo | Origen | Propuesta canónica |
|---|---|---|
| `symbol` | columna de `X` | `(create symbol <id> <sign>)` |
| `implication` | arco `a → b` del grafo | `(if a b)` → fila de `I` |
| `class` | clase de nivel significativo | `(create wigame <hijo> <li>)` + `RoutingProjection` al padre |
| `nonsense` | par sin co-ocurrencia con soporte | `S_i[a,b] = unsinnig` |

Más adelante, AROMA añade `projection` (concepto de un mundo → concepto de otro).

## 3. Flujo

```
sia/report ──► cola (proposed) ──► LLM: redacta (R a b), resuelve sinónimos,      ──► humano: confirm / reject / edit
                                        sugiere WiGame destino, adjunta cita           │
                                                                                       ▼
                                                              (promote <candidate-id> [tier])  →  Fact.evidence.curation=confirmed, truth=TRUE
```

- **Estados** en `Fact.evidence.curation`: `proposed | confirmed | rejected`. Un `rejected` se conserva (evita re-proponer lo mismo).
- **Umbrales por `φ`** (calibrables): `φ ≥ 0.99` → puede auto-confirmarse si además supera `n_min` de soporte; `0.85 ≤ φ < 0.99` → cola; `φ < 0.85` → no se propone.
- **El LLM no decide verdad.** Recibe el candidato, las oraciones citadas por `Prov(f)` y el vocabulario del `WiGame`; devuelve la S-expression canónica, la cita elegida y un comentario. Su salida es un `proposed` mejor formado, nunca un `confirmed`. Implementado en `pipeline/curate.py`: `propose(system, candidate_id, backend, documents)` escribe la propuesta en `evidence.llm` y no toca `curation`; backends `PiBackend` (`pi -p --no-tools`, deepseek-flash) y `FakeBackend` (tests); CLI `python -m pipeline.curate <corpus> --wigame <id> --backend pi|fake`; en el REPL, `sugiere <id>`.
- **El humano ve** la regla, el `φ`, las oraciones fuente y la S-expression, y responde con una tecla. Todo queda en `evidence`.

## 4. Casos que exigen curado obligatorio

- **`unsinnig`:** la ausencia de co-ocurrencia en el corpus no demuestra absurdo. Solo un humano marca `S_i = unsinnig`.
- **Proyecciones entre mundos:** `RoutingProjection` es `entidad × entidad` (`matrix/src/operational_model/routing/routing_projection.py:13`); CHIC/AROMA entregan `concepto × concepto`. El paso a instancias se propone (LLM) y se confirma (humano).
- **Símbolos nuevos que colisionan** con `signs` ya registrados en `LogicalSystem.names`: el LLM propone `equivalent` o un `symbol_id` distinto; el humano decide.

## 5. Interfaz

- `(return candidates [wigame:<id>] [tier:<t>] [min-phi:<x>])` — lista la cola.
- `(promote <candidate-id> [tier:<observed|confirmed>])` — confirma: escribe `V_i`/`S_i`/`I` según el tipo y actualiza `evidence`.
- `(reject <candidate-id> "<motivo>")`.
- `(why (R a b))` — devuelve la cadena de implicaciones que la sostiene y las citas de cada premisa (ver [shrdlu.md](shrdlu.md)).

Estos verbos se añaden al runtime existente (ver [runtime_api.md](runtime_api.md)).

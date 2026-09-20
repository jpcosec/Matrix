# Grounding y curado

## 1. Principio

No hay mapeo automático texto → ontología. Lo que se garantiza es: **todo hecho puede referenciarse
a su fuente** (`Prov(f)`, [provenance.md](provenance.md)) y **nada pasa de `UNKNOWN` a `TRUE` sin una
decisión registrada**. El curado se automatiza al máximo, pero el paso final lo dan un LLM que
propone y un humano que confirma.

## 2. Candidatos

La convergencia ([convergence.md](convergence.md) §3) y el mantenimiento de `W_i` producen cuatro
tipos de candidato, cada uno con `Prov(f)` y sus estadísticos (`φ`, `n_st`, contextos):

| Tipo | Origen | Propuesta canónica |
|---|---|---|
| `projection` | par `s → t` con `φ ≥ φ_min` entre símbolos de contextos distintos | `(project wigame:<src> wigame:<dst> (s t) …)` (una `RoutingProjection`) |
| `equivalent` | `φ ≥ 0.95` en ambos sentidos | `(equivalent s t)`: los dos símbolos comparten referente (`ref:<k>`) |
| `gate` | columna tautológica de `V_i` en un `WiGame` | `class` con `payload={gate, symbols}`: la coordenada no discrimina y se propone como compuerta `C_k` |
| `D_i` | pares de sujetos indistinguibles en `V_i` | dimensión discriminativa propuesta por la jerarquía de `sia` sobre `sujetos × coordenadas`; si ninguna coordenada los separa, queda `unresolved` |

Los hechos que declara un contexto (`pipeline/decompose.py`) no son candidatos: son
**`observed`** de ese juego de lenguaje, con `Prov(f)` = span de la oración. La ambigüedad de un
signo entre contextos no es un error: es el estado normal y lo resuelve la convergencia.

## 3. Flujo

```
texto ─► chunks (contextos) ─► declaraciones por contexto (heurística o LLM) ─► WiGames (observed)
                                              │
                        converge_in_batches (lotes = mantenimiento de W_i)
                                              ▼
                        candidatos projection / equivalent / gate / D_i (proposed)
                                              │
                        LLM descompone y redacta la propuesta; el humano decide
                                              ▼
                        (promote …) ⇒ curation=confirmed; (reject …) ⇒ rejected y se conserva
```

- **Estados** en `Fact.evidence.curation`: `proposed | confirmed | rejected`. Un `rejected` se
  conserva (evita re-proponer lo mismo).
- **Regla de promoción automática**: `equivalent` si `φ ≥ 0.95` en ambos sentidos, `projection` si
  `φ ≥ 0.95` en un sentido, con ≥ 2 configuraciones informativas compartidas y ≥ 2 contextos
  (intra-contexto: basta ≥ 2 configuraciones). Es la única vía automática; todo lo demás espera
  curado.
- **El LLM no decide verdad.** Actúa como **descompositor de superficie** (`pipeline/decompose.py`,
  `pipeline/decompose_batch.py`): una llamada por chunk, con los signos locales y las familias de
  relación; no resuelve pronombres, no inventa símbolos ni relaciones. Sobre los candidatos
  (`pipeline/curate.py`) redacta la S-expression, elige la cita y comenta; su salida es un
  `proposed` mejor formado.
- **El humano ve** la regla, el `φ`, las configuraciones compartidas, las oraciones fuente y la
  S-expression, y responde con una tecla (`aprueba` / `rechaza`).

## 4. Casos que exigen curado obligatorio

- **`unsinnig`:** la ausencia de co-ocurrencia en el corpus no demuestra absurdo. Solo un humano
  marca `S_i = unsinnig` (el silencio no es absurdo).
- **Proyecciones entre mundos:** entre `WiGame`s son entidad × entidad
  (`matrix/src/operational_model/routing/routing_projection.py:13`); AROMA o el LLM entregan
  concepto × concepto. El paso a instancias se propone y se confirma.
- **Símbolos nuevos que colisionan** con `signs` ya registrados: el LLM propone `equivalent` o un
  `symbol_id` distinto; el humano decide.

## 5. Interfaz

- `(return candidates [wigame:<id>] [tier:<t>] [curation:<c>] [min-phi:<x>])` — lista la cola.
- `(promote <candidate-id> [tier:<observed|confirmed>])` — confirma: escribe `V_i`/`S_i`/`I` o
  rellena la proyección según el tipo y anota `history`.
- `(reject <candidate-id> "<motivo>")`.
- `(why …)`, `(ask …)`, `(retract …)` — ver [runtime_api.md](runtime_api.md).

## 6. Resultados del curado automático

En `corpus/physicists` (régimen `pairs`, ver [convergence.md](convergence.md) §7): el descompositor
LLM propone 11 242 declaraciones, la convergencia promueve 45 candidatos y deja 296 `proposed`; la
basura plantada (50 hechos falsos) queda aislada en el 100 % de los casos frente al 96 % de los
hechos reales. El cuello de botella es la capa de declaraciones (cantidad y lexicalización de los
objetos), no la promoción.

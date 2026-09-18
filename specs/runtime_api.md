# Runtime API — S-expressions

Superficie única de mando del motor. Forma canónica `(R a b)`; selectores `kind:value` (`wigame:vegetales`, `symbol:lechuga`, `relation:es`). Toda operación devuelve `OperationResult(status, sinn, payload, reason)` con `status ∈ {accept, reject, ambiguous}` (`matrix/src/operational_model/system/operation_results.py`). Errores de sintaxis lanzan `ValueError`.

## 1. Verbos existentes (`system/s_expression_runtime.py`)

| Verbo | Efecto | Payload |
|---|---|---|
| `(check [wigame:<id>] (R a b))` | consulta `V_i` | `{wigame_id, proposition, truth, exists}`; sin `wigame` y varios candidatos → `ambiguous` + `candidates` |
| `(assert [wigame:<id>] (R a b))` | escribe `TRUE` en `V_i` | `{action: added|noop}`; celda `FALSE` → `reject`, `sinn=widerspruechlich`; sin mundo que acepte → `reject`, `unsinnig` |
| `(ingest wigame:<id> (R a b))` | registra la proposición sin verdad | `{action: registered}` |
| `(create symbol <id> <sign>)` · `(create relation <id> <name> [commutative:true …])` · `(create li <id> <rel> (axis-a …) (axis-b …))` · `(create wigame <id> <li> [context:<id>])` | catálogo | `{…, action}` |
| `(return facts [symbol:<x>] [relation:<r>] [wigame:<w>])` | lista hechos | `{groups: [{wigame_id, facts: [...]}]}` |

## 2. Verbos nuevos

| Verbo | Efecto | Notas |
|---|---|---|
| `(assert … (R a b) [evidence:<json>])` | como hoy, con `evidence` opcional | por defecto `tier=observed`, `curation=confirmed` |
| `(retract [wigame:<id>] (R a b) [to:false|unknown] "<motivo>")` | `V_i ← FALSE` (defecto) o `UNKNOWN`; anota `history` | no borra el `Fact`; si hay hechos `inferred` que dependen de él, los devuelve en `payload.dependents` y los pasa a `UNKNOWN` |
| `(return candidates [wigame:<id>] [tier:<t>] [min-phi:<x>])` | cola de curado | ver [grounding.md](grounding.md) |
| `(promote <candidate-id> [tier:confirmed|observed])` | aplica el candidato: `V_i`, `S_i` o fila de `I`; `curation=confirmed` | rechazo explícito si contradice `V_i` |
| `(reject <candidate-id> "<motivo>")` | `curation=rejected`, se conserva | |
| `(why [wigame:<id>] (R a b))` | cadena de justificación | `{chain: [{fact, tier, prov, rule}]}`; para `observed` devuelve solo `prov` |
| `(define (if (R a b) (R c d)))` | añade la regla a `system.rules` con `tier=observed` y ejecuta `deduce` en los mundos que aceptan ambas proposiciones | los símbolos nuevos se crean antes con `create symbol`; ambas proposiciones deben usar la relación del `LiSpace` del mundo (un `LiSpace` admite una sola relación) |
| `(project wigame:<src> wigame:<dst> (a b) …)` | escribe celdas de `RoutingProjection` | solo desde curado |

## 3. Reglas

- Nunca se elige un `WiGame` en silencio: `ambiguous` obliga a repetir con `wigame:<id>`.
- `UNKNOWN` no participa en `modus_ponens`; `promote` es la única vía de `UNKNOWN → TRUE` para hechos `statistical`.
- Contradicciones: señal explícita y las tres políticas de [provenance.md](provenance.md) §3.
- Ingesta masiva desde `sia/report`: un script emite las S-expressions (`create …`, `ingest …`, candidatos) y las pasa por `SExpressionRuntime.evaluate` una a una; la atomicidad es por comando.

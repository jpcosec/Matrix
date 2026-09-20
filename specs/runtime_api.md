# Runtime API — S-expressions

Superficie única de mando del motor. Forma canónica `(R a b)`; selectores `kind:value` (`wigame:vegetales`, `symbol:lechuga`, `relation:es`). Toda operación devuelve `OperationResult(status, sinn, payload, reason)` con `status ∈ {accept, reject, ambiguous}` (`matrix/src/operational_model/system/operation_results.py`). Errores de sintaxis lanzan `ValueError`.

## 1. Verbos existentes (`system/s_expression_runtime.py`)

| Verbo | Efecto | Payload |
|---|---|---|
| `(check [wigame:<id>] (R a b))` | consulta `V_i` | `{wigame_id, proposition, truth, exists}`; sin `wigame` y varios candidatos → `ambiguous` + `candidates` |
| `(assert [wigame:<id>] (R a b))` | escribe `TRUE` en `V_i` | `{action: added|noop}`; celda `FALSE` → `reject`, `sinn=widerspruechlich`; sin mundo que acepte → `reject`, `unsinnig` |
| `(ingest wigame:<id> (R a b))` | registra la proposición sin verdad | `{action: registered}` |
| `(create symbol <id> <sign>)` · `(create relation <id> <name> [commutative:true …])` · `(create li <id> <rel> (axis-a …) (axis-b …))` · `(create wigame <id> <li> [context:<id>])` · `(create context <ctx-id> [parent:<ctx-id>])` | catálogo; el contexto registra un `Context` y, con `parent:`, la ruta padre → hijo | `{…, action}` |
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
| `(define (if (and (R a b) (R c d) …) (R e f)))` | regla conjuntiva: el átomo compuesto entra en `v` cuando todos sus conjuntos son TRUE; `derived_from` recoge todos | R-reglas de grado > 1 en forma ground |
| `(project wigame:<src> wigame:<dst> (s t) (s2 t2) …)` | enlaza celdas de la `RoutingProjection` `src->dst` (la crea si no existe) con `tier=observed` | |
| `(candidate projection wigame:<src> (wigame:<dst> (s t) …) evidence:<json>)` | candidato de proyección (los genera `pipeline/convergence.py` a partir de la convergencia de símbolos) | `promote` enlaza los pares |
| `(return projections [wigame:<src>])` | `{projections: [{source, target, pairs}]}` | |

## 3. Consultas ruteadas y convergencia

`(check …)` responde sobre un solo juego. Para preguntar **cruzando juegos** está
`pipeline.query.ask(system, relation, subject_symbol, object_norm=None, hops=2)`, que parte del
mundo del sujeto, sigue las proyecciones promovidas en el sentido en que existen (transportando el
grupo de referentes), recoge los hechos `(R s' b)` TRUE y devuelve `Answer(objects, path,
truth_for)` con `true | false | ∅`. El REPL la usa para las preguntas en inglés y español; no es un
verbo S-expression.

`deduce(system)` sin `wigame_id` opera sobre todos los mundos: cada átomo nuevo se inserta en el mundo que lo acepta; si lo aceptan varios queda en `ambiguous` (no se inserta) y si ninguno en `unplaced`. Así una regla puede concluir en otra relación sin que un `LiSpace` tenga que admitir varias.

## 4. Reglas

- Nunca se elige un `WiGame` en silencio: `ambiguous` obliga a repetir con `wigame:<id>`.
- `UNKNOWN` no participa en `modus_ponens`; `promote` es la única vía de `UNKNOWN → TRUE` para hechos `statistical`.
- Contradicciones: señal explícita y las tres políticas de [provenance.md](provenance.md) §3.
- La convergencia (`pipeline/convergence.symbol_convergence` / `converge_in_batches`) escribe las
  S-expressions (`create …`, candidatos) y las pasa por `SExpressionRuntime.evaluate` una a una; la
  atomicidad es por comando. Los lotes son el mantenimiento de `W_i` de
  [convergence.md](convergence.md) §4.

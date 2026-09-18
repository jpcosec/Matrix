# SHRDLU — el loop de interacción

Del SHRDLU de Winograd (1972; fuente en `sources/shrdlu/consoleshrdlu/`, 19.1k líneas de MACLISP) no se copia el planificador ni el mundo de bloques: se copia **cómo se conversa con él**. La diferencia es que nuestros mundos son lógicos y **poblables**: un comando no mueve bloques, afirma o retracta hechos, crea símbolos y reglas.

## 1. Los cinco comportamientos

### 1.1 Aclaración ante ambigüedad
Original: `NEWANS` (`AMBIG`, `PARSE-ASSOC`) detecta varias interpretaciones y pregunta.
Aquí: si `(R a b)` cabe en más de un `WiGame`, o un signo resuelve a más de un `Symbol`, el runtime ya devuelve `status="ambiguous"` con `candidates`. El loop lo convierte en pregunta y guarda la respuesta como preferencia del diálogo.
```
> la lechuga tiene hoja rugosa
? "hoja rugosa" puede ser hoja.rugosa (wigame:vegetales) o rugosa (wigame:texturas). ¿Cuál?  [1/2]
> 1
= (assert wigame:vegetales (has_property lechuga hoja.rugosa)) → accept
```

### 1.2 Memoria de eventos: *why / how / when*
Original: `SYSCOM` `EVENTLIST` y `NEWANS` `DESCRIBEVENT` encadenan cada subobjetivo con el comando que lo causó (`'WHY`).
Aquí: cada hecho inferido guarda `derived_from`; cada hecho confirmado guarda `prov`. `why` recorre la cadena.
```
> ¿por qué la lechuga es verdura?
= (why (es lechuga verdura))
  porque (has_property lechuga hoja) [confirmed; "…la lechuga, de hoja…" recetas/ensaladas.md:212-240]
  y (if has_property.hoja es.verdura) [confirmed; φ=0.93, 118 oraciones]
```

### 1.3 Definir conceptos en caliente
Original: `DICTIO` `#DEFINE/#NEWWORD` ("a steeple is a stack which contains two green cubes and a pyramid"); `PLNR` `THDEF/THCONSE`.
Aquí: `define` crea símbolo, relación o regla, con `tier=observed` y el humano como fuente.
```
> una verdura de hoja es una verdura que tiene hoja
= (define verdura_de_hoja (and (es ?x verdura) (has_property ?x hoja)))
  → (create symbol verdura_de_hoja …) + (if (and es.verdura has_property.hoja) es.verdura_de_hoja) en I
```

### 1.4 Anáfora y foco del discurso
Original: `SMUTIL`/`SMSPEC` mantienen referentes y resuelven "it", "the one I told you to pick up".
Aquí: `DialogState` pasa de guardar el último referente (`prototypes/shrdlu/dialog_state.py`, 24 líneas) a una pila de referentes con tipo, el `WiGame` en foco y las aclaraciones previas.
```
> ¿la espinaca tiene raíz?        = (check wigame:vegetales (has_property espinaca raiz)) → FALSE
> ¿y hoja?                        = (check wigame:vegetales (has_property espinaca hoja)) → TRUE
```

### 1.5 Consola de introspección
Original: cuatro estados (`READY/RUN/COMMAND/REQUEST`) y árboles `SHOW`/`TELL` (`HELP`, `SHOW`, `SYSCOM`).
Aquí: comandos de sistema en el mismo REPL: `show wigame <id>`, `show candidates`, `show why <fact>`, `tell threshold 0.9`, `tell unit paragraph`.

## 2. Lo que no se copia

El Micro-Planner (`PLNR`, `THTRAC`: metas con backtracking) lo reemplaza el punto fijo booleano `v ⊗ I*` del kernel. `GRAMAR`/`PROGMR` (gramática sistémica del inglés) se sustituyen por el parser controlado del prototipo y, más adelante, por un LLM que *solo* traduce a S-expressions.

## 3. Rol del LLM

Traduce la frase del usuario a una S-expression canónica y verbaliza el `OperationResult`. **No decide verdad ni sentido**: si emite `(assert …)` de algo `unsinnig`, `S_i` lo rechaza; si emite algo no confirmado, entra como `proposed`. La integración con entrenamiento o inferencia interna de LLMs no existe y no se promete (átomo `Integracion_LLM…_Aun_No_Demostrada` de Matrix).

## 4. Implementación

`matrix/prototypes/shrdlu/` (léxico, parser, frames, lowering) es el punto de partida; se añade `dialog_state.py` real, un `repl.py` con los comandos de sistema y el mapeo de `OperationResult` a respuestas. Tests en `matrix/tests/test_shrdlu_*.py` (ya en verde).

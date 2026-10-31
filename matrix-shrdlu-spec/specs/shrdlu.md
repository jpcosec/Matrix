# SHRDLU — el loop de interacción

Del SHRDLU de Winograd (1972; fuente en `sources/shrdlu/consoleshrdlu/`, 19.1k líneas de MACLISP) no
se copia el planificador ni el mundo de bloques: se copia **cómo se conversa con él**. La diferencia
es que nuestros mundos son lógicos y **poblables**: un comando no mueve bloques, afirma o retracta
hechos, crea símbolos y reglas. El Micro Planner (`PLNR`, `THTRAC`) con backtracking se sustituye por
el punto fijo booleano `v ⊗ I*`, y la gramática sistémica (`GRAMAR`, `PROGMR`) por un descompositor
de superficie (heurístico o LLM barato) que traduce a S-expressions canónicas.

El estado del diálogo vive en `matrix/prototypes/shrdlu/dialog_state.py` (`focus_wigame`,
`last_subject`, `last_object`, `last_verb`, `pending`, `answer(choice)`), no en la memoria del chat.

## 1. Los cinco comportamientos

### 1.1 Aclaración ante ambigüedad
Original: `NEWANS` (`AMBIG`, `PARSE-ASSOC`) detecta varias interpretaciones y pregunta.
Aquí: un signo existe en **varios contextos** (es el estado normal), así que el REPL pregunta con
opciones numeradas y `answer("1")` resuelve la S-expr pendiente. El runtime devuelve
`status="ambiguous"` con `candidates` cuando `(R a b)` cabe en más de un `WiGame`.
```
> ¿la lechuga tiene hoja?
«lechuga / hoja» es ambiguo: 1) lechuga@01_lechugas + hoja@01_lechugas | 2) … + hoja@02_espinacas | 3) … + hoja@05_hojas. ¿Cuál? [1-3]
> 1
Sí: (has_property lechuga@01_lechugas hoja@01_lechugas) [corpus/vegetales/01_lechugas.md:…] · ruta: wigame:01_lechugas:has_property
```

### 1.2 Memoria de eventos: *why / how / when*
Original: `SYSCOM` `EVENTLIST` y `NEWANS` `DESCRIBEVENT` encadenan cada subobjetivo con el comando
que lo causó (`'WHY`).
Aquí: cada hecho inferido guarda `derived_from` y cada hecho declarado guarda `prov`; `why` recorre
la cadena.
```
> ¿por qué la lechuga tiene hoja_lisa?
porque (has_property lechuga@01_lechugas hoja_lisa@01_lechugas) [observed; corpus/vegetales/01_lechugas.md:14-38]
```

### 1.3 Definir conceptos en caliente
Original: `DICTIO` `#DEFINE/#NEWWORD`; `PLNR` `THDEF/THCONSE`.
Aquí: `(define (if (R a b) (R c d)))` (o con `and`) añade la regla a `system.rules` con
`tier=observed` y ejecuta `deduce` sobre todos los mundos; los símbolos nuevos se crean antes con
`create symbol`.
```
> si la lechuga tiene hoja_lisa entonces la lechuga tiene verde
Regla añadida. Derivados: (has_property lechuga@01_lechugas verde@01_lechugas).
```

### 1.4 Anáfora y foco del discurso
Original: `SMUTIL`/`SMSPEC` mantienen referentes y resuelven "it", "the one I told you to pick up".
Aquí: `DialogState` guarda el último sujeto, objeto y verbo, y resuelve la elipsis «¿y Z?» repitiendo
el verbo sobre el último sujeto.
```
> ¿la lechuga tiene hoja_lisa?      = (ask has_property lechuga@01_lechugas hoja_lisa@01_lechugas)
> ¿y raíz?                          = (ask has_property lechuga@01_lechugas raiz@03_zanahorias)
```

### 1.5 Consola de introspección
Original: cuatro estados (`READY/RUN/COMMAND/REQUEST`) y árboles `SHOW`/`TELL` (`HELP`, `SHOW`,
`SYSCOM`).
Aquí: `show wigame` lista los hechos, `tell foco <x>` cambia el foco, `candidatos` / `aprueba <id>` /
`rechaza <id> <motivo>` operan sobre la cola de curado, y `sugiere <id>` pide una propuesta al
backend LLM (nunca confirma).

## 2. Preguntas naturales

- Inglés simple (sin LLM): `was X born in Y?`, `did X win Y?`, `what did X discover?` →
  `pipeline/query.ask`, que sigue las proyecciones promovidas y responde con ruta y cita. Un signo
  que existe en varios contextos prueba todos los símbolos compatibles y usa el que responde; el
  `why?` pelado explica el último turno.
  ```
  > was Curie born in Warsaw?          # corpus/physicists/en, --lang en
  Sí: (born_in curie@Q7186 warsaw@Q7186) [corpus/physicists/en/Q7186.md:938-962] · ruta: wigame:Q7186:born_in
  > why?
  porque (born_in curie@Q7186 warsaw@Q7186) [observed; corpus/physicists/en/Q7186.md:938-962]
  ```
- Español controlado: `¿X tiene Y?` → `ask` con la relación del verbo (`tiene`→`has_property`,
  `es`→`instance`, `lleva`→`part_of`); `¿por qué …?` → `why`; `X ya no tiene Y` → `retract` sobre
  `wigame:<ctx>:<R>`.

## 3. Lo que no se copia

`GRAMAR`/`PROGMR` (gramática sistémica del inglés) se sustituyen por el descompositor controlado y,
más adelante, por un LLM que *solo* traduce a S-expressions. El Micro Planner no se copia: la
deducción es el punto fijo booleano.

## 4. Rol del LLM

Traduce la frase del usuario a una S-expression canónica y verbaliza el `OperationResult`. **No
decide verdad ni sentido**: si emite `(assert …)` de algo `unsinnig`, `S_i` lo rechaza; si emite
algo no confirmado, entra como `proposed`. La integración con entrenamiento o inferencia interna de
LLMs no existe y no se promete.

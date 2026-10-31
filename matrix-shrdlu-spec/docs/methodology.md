# Metodología de pruebas

Qué se probó en este repositorio, por qué se hizo cada prueba, cómo se hizo, y cómo diseñar una
prueba nueva. Complementa `docs/technical.md`, que describe el código y lista los resultados.

## 1. Criterios generales

Todas las pruebas del repositorio siguen las mismas reglas. Están aquí porque cada una salió de un
error concreto.

1. **Se prueba una capa a la vez.** El sistema tiene capas (signos, declaraciones, ingesta,
   propuestas, consulta). Una métrica de extremo a extremo no dice qué capa falló, así que cada
   evaluación reporta además variables intermedias: declaraciones por ocurrencia, configuraciones
   compartidas por par correcto, pares candidatos.
2. **La verdad de referencia viene de fuera de la cadena.** Referentes conocidos por construcción
   (sintético), identidad de artículo y hechos de Wikidata (físicos), o alias escritos por una persona
   (KB de Matrix). Nunca la salida de otra etapa del mismo sistema.
3. **Siempre hay un control positivo y uno negativo.** Positivo: un caso donde el resultado correcto
   es alcanzable por construcción (corpus sintético). Negativo: material que no debe producir nada
   (hechos falsos plantados, personas distintas).
4. **Los parámetros se fijan antes de medir y no se ajustan después.** Si una prueba cambia un
   parámetro, el cambio es la variable del experimento y se reportan todas las configuraciones.
5. **Se reporta lo que salga.** Los resultados nulos y las fusiones falsas van al informe con
   ejemplos concretos.
6. **Todo es determinista y repetible.** Orden fijo de proceso, salidas de LLM cacheadas en el
   corpus, corpus versionado. Una evaluación no usa red.
7. **Tope de recursos.** Toda corrida pesada va con `bash scripts/capped.sh <GB> -- …`, una corrida
   por comando, con `timeout`, y escribe métricas parciales tras cada etapa.
8. **Se evalúa cada componente por el papel que tiene.** La capa estadística propone; no decide. Se
   mide como proponente: cuántas consultas tienen candidato, en qué posición queda el correcto, y
   cuántos vínculos falsos ofrece con puntaje alto.

## 2. Niveles de prueba

| Nivel | Dónde | Qué garantiza | Duración |
|---|---|---|---|
| Unitario | `tests/test_sia_*`, `test_populator_*`, `test_contexts`, `test_decompose*` | cada función hace lo que dice, contra valores calculados a mano o publicados | milisegundos |
| Fixture con verdad conocida | `tests/test_convergence*`, `test_ingest`, `test_query` | el comportamiento conjunto sobre un mundo pequeño donde se sabe la respuesta | segundos |
| Humo | `tests/test_eval_smoke`, `test_eval_matrix_kb` | los scripts de evaluación corren de principio a fin con `--limit` y escriben las claves esperadas | segundos |
| Evaluación | `experiments/eval_physicists.py`, `eval_matrix_kb.py` | mediciones sobre corpus reales; no son tests de `pytest`, producen `metrics.json` y `report.md` | segundos a minutos |

Los tres primeros niveles corren en `pytest` (`tests/` aquí y `../tests/` para el motor). Los tests que
dependen de un corpus o de una ruta externa usan `pytest.skip` si no existe.

## 3. Pruebas unitarias

### 3.1 `sia/`: fórmulas contra el libro

- **Por qué.** `sia` se implementó desde el libro de SIA sin una implementación de referencia. Un
  error en una fórmula contamina todo lo que se mida después.
- **Cómo.** `test_sia_intensity` reproduce la Tabla 1 (p. 22) con tolerancia 1e-3: caso (a)
  `ϕ = 0.9999, τ = 0, φ = 0`; caso (b) `τ = 0.6035, φ = 0.777`; caso (c) misma proporción con `n`
  menor da menor intensidad. Casos límite: `ϕ = 0` cuando `n_b = n`; Poisson exacta cuando `λ ≤ 4`.
  `test_sia_cohesion`: 0 si `ϕ ≤ 0.5`, 1 si `ϕ = 1`, monótona, y la cohesión de clase contra la media
  geométrica calculada a mano. `test_sia_hierarchy` reproduce las clases de la Figura 1 (p. 26) y
  compara `significant_levels` con una implementación ingenua. `test_sia_graph` comprueba que el grafo
  no infiere arcos transitivos (ejemplo de la p. 34). `test_sia_similarity` y `test_sia_aroma` usan
  los mismos bloques.
- **Criterio de diseño.** Cuando existe un valor publicado, el test lo usa. Cuando no, se compara
  contra una versión ingenua y lenta de la misma función.

### 3.2 `populator/`: signos y offsets

- **Por qué.** Cada hecho cita su origen por offset de carácter. Un offset corrido invalida la cita y
  no produce ningún error visible.
- **Cómo.** `test_populator_extract` y `test_contexts` verifican que `texto[span]` devuelve
  exactamente el signo, que limpiar el markdown conserva los offsets, y que las oraciones no se cortan
  en `;` ni dentro de paréntesis. `test_contexts` fija además las reglas de signos: el mismo signo en
  dos contextos son dos ocurrencias, los nombres no se pliegan entre sí, los pronombres se conservan,
  las ventanas de nombre admiten conectores y no cruzan puntuación, el nombre del archivo nunca es
  signo.
- **Origen de cada test.** Casi todos salieron de un defecto visto en datos reales: un sujeto
  `1934@Q7186` por un corte en `;`, `q7186` como signo, `University of Paris` partido en tres.
  La regla: **todo defecto encontrado en un corpus se convierte en un test unitario con la oración
  que lo produjo.**

### 3.3 `pipeline/decompose*`: declaraciones

- **Por qué.** La capa de declaraciones es la entrada de todo lo demás, y el descompositor LLM no es
  confiable por defecto.
- **Cómo.** `test_decompose` usa oraciones concretas y afirma las tripletas exactas: núcleo del
  sintagma nominal en la cópula, modificadores como `has_property`, fechas en `born_in`, variante
  canónica `nobel_prize`, nombre completo de universidad en `employer`, y que el respaldo `rel:<verbo>`
  nunca use un nombre propio como verbo. Dos invariantes: las declaraciones solo usan signos del
  propio contexto, y sus spans apuntan dentro del documento. `test_decompose_llm_chunk` usa un
  `FakeBackend`: JSON válido, tripletas con signos ajenos (se descartan), JSON envuelto en prosa (se
  acepta), JSON roto (un reintento), y la caché (segunda llamada con backend contador en cero).
- **Criterio de diseño.** El LLM nunca se llama en un test. Se prueba el contrato: qué se le pide,
  qué se acepta y qué se rechaza.

### 3.4 `pipeline/ingest`, `query`, `curate`

- `test_ingest`: existen contextos, ocurrencias y juegos; un hecho lleva su procedencia; los juegos
  son contextos cerrados; `part_of` es transitiva y `spouse` conmutativa; una contradicción plantada
  se rechaza. Por qué: comprobar que la ingesta pasa por el runtime de Matrix y no lo esquiva.
- `test_query`: `ask` sigue una proyección a otro contexto, no devuelve hechos de la otra persona,
  `why` devuelve la procedencia del contexto ajeno, una proyección en un solo sentido se sigue solo en
  ese sentido.
- `test_curate`: el prompt incluye el tipo de propuesta y las configuraciones compartidas; `propose`
  nunca cambia el estado de curado por sí mismo.

## 4. Pruebas con verdad conocida

### 4.1 Corpus sintético Curie/Franklin

- **Por qué.** Hacía falta un caso donde se supiera qué ocurrencia es de quién y qué hechos son
  falsos, para distinguir «el algoritmo no funciona» de «el texto no trae evidencia». Es el control
  positivo de todo el repositorio.
- **Cómo se construyó** (`tests/fixtures/curie_franklin.py`). 30 artículos generados: 15 sobre Marie
  Curie y 15 sobre Rosalind Franklin. Se eligieron dos mujeres para que el pronombre `she` sea
  homónimo entre los dos grupos. Cada persona tiene 24 hechos nucleares, 8 por cada forma de sujeto
  (nombre completo, apellido, `she`), más 2 hechos variables con sujetos ajenos. Se plantan 10 hechos
  falsos `born_in she Tokyo_k`, uno por artículo, muestreados sin reemplazo para que ninguna
  ocurrencia tenga más de un contraejemplo. El generador recibe una semilla.
- **Qué se afirma** (`test_convergence.py`).
  - Jerarquía de contextos: varios nodos y ninguno mezcla los dos grupos.
  - Al menos el 80 % de los `she@curie_i` queda en un grupo que contiene `marie_curie@` o `curie@`.
  - Ningún `she@franklin` comparte grupo con ocurrencias de Curie.
  - Las 10 ocurrencias plantadas no aparecen en ninguna propuesta ni grupo, y al menos 8 tienen
    puntaje menor que 0.5.
  - Una segunda corrida no promueve nada.
- **Decisiones del diseño.** El umbral es 80 % y no 100 % para que el test no dependa de un artículo.
  El fixture repite su núcleo de hechos en cada artículo, así que estos tests pasan `taut_df=1.0`; con
  el filtro activo esos hechos se descartarían por frecuentes. El número de hechos por forma de sujeto
  salió de una cuenta previa: con 5 configuraciones la intensidad máxima es 0.965 y con 8 supera el
  umbral con holgura.
- **Qué no prueba.** Que el texto real traiga ese soporte. El sintético es favorable por
  construcción.

### 4.2 Corpus de vegetales

- **Por qué.** Reproducir el ejemplo del paper de Matrix (lechuga, espinaca, zanahoria, apio) con
  `maintain_wigame`.
- **Cómo.** `test_vegetales_gate_on_verde`: `verde` sale como compuerta del juego de lechugas.
  `test_collision_discriminant_is_a_leaf`: el par lechuga/espinaca colisiona y su discriminante es
  `hoja_lisa`/`hoja_rugosa`. `test_collision_without_leaf_features_is_unresolved`: sin esas dos
  coordenadas el par se reporta como no resuelto. El segundo y el tercero usan un mundo mínimo
  construido en el test, porque el corpus real no tiene un juego con ambos sujetos.

### 4.3 Equivalencia y escala tras el rediseño por pares

- **Por qué.** El cálculo denso p×p mató el ambiente tres veces por falta de memoria. El reemplazo
  tenía que dar los mismos números.
- **Cómo** (`test_convergence_pairs.py`).
  - Oráculo: la intensidad por pares coincide con la densa anterior para todos los pares candidatos
    del sintético, `atol=1e-9`.
  - Lotes: `converge_in_batches(batch_size=5)` produce las mismas particiones que la corrida completa.
  - Escala: 3 000 ocurrencias en 300 contextos, pico de `tracemalloc` < 200 MB y tiempo < 20 s
    (mide 16 MB y 3.2 s).
  - Continuar un informe previo no duplica grupos ni promociones.
- **Regresión sobre datos reales.** Antes del cambio se guardaron las métricas de `heuristic` y `llm`
  (`*.before`) y después se compararon campo a campo. Las diferencias se explicaron una por una en
  `.herdr/agglomerative_report.md`.
- **Criterio de diseño.** Un cambio de rendimiento se prueba con tres cosas: igualdad numérica contra
  la versión vieja, un límite explícito de memoria y tiempo, y comparación de métricas sobre datos
  reales.

### 4.4 El tope de memoria

- **Por qué.** Nada impedía que un proceso de un worker tumbara la terminal.
- **Cómo.** Se corrió bajo `capped.sh 1` un script que reserva 3.2 GB. Resultado esperado y obtenido:
  exit 137 para ese proceso y la shell intacta.

## 5. Evaluaciones sobre corpus reales

### 5.1 Elección del corpus de físicos

- **Por qué este corpus.** Se necesitaban textos cortos sobre entidades con verdad de referencia
  externa, pronombres, homónimos y menciones cruzadas, con licencia libre. Simple English Wikipedia
  da artículos cortos de sintaxis simple; Wikidata da hechos por entidad; la Wikipedia en inglés da
  una segunda fuente sobre la misma persona; GAP es un corpus de correferencia de pronombres.
- **Cómo se construyó** (`corpus/physicists/build.py`). Consulta SPARQL por ocupación físico o
  subclase, nacidos 1850-1900, con artículo en Simple English: 103 personas. Se excluyen los artículos
  de menos de 300 caracteres: quedan 89. La consulta exacta sin subclases daba 79, bajo el mínimo de
  80 que se había fijado. Un extracto por petición, porque la API devuelve uno solo aunque se pidan
  varios títulos. `tests/test_corpus_physicists.py` fija la forma del corpus.
- **Lo que no sirvió.** GAP: ninguna de sus páginas trata de un físico del corpus, cobertura 0. Se
  conserva y se reporta así.

### 5.2 Régimen `document`

- **Pregunta.** ¿Qué propone la capa con un contexto por persona?
- **Cómo.** 89 contextos, métricas de QA contra Wikidata, pronombres y basura.
- **Resultado y consecuencia.** 0 promociones. Con un solo contexto por entidad no hay segunda fuente
  con la que comparar. Motivó el régimen por secciones.

### 5.3 Régimen `section`

- **Hipótesis.** Las secciones de un artículo largo son varios contextos sobre la misma persona.
- **Cómo.** Artículos de la Wikipedia en inglés partidos en `## `; 564 contextos. Métricas nuevas:
  vínculo entre secciones del mismo artículo, fusiones falsas entre artículos sin mención cruzada, QA
  con salto entre secciones.
- **Resultado y consecuencia.** Vínculo entre secciones 0.0: el encabezado y cada sección cuentan
  hechos distintos, así que sus configuraciones son disjuntas. Una fusión falsa entre dos `it`. De
  aquí salieron la guarda de 2 configuraciones compartidas y el régimen `pairs`.

### 5.4 Régimen `pairs`

- **Hipótesis.** Dos textos independientes sobre la misma persona repiten hechos.
- **Cómo.** 178 contextos: artículo Simple más encabezado en inglés de la misma persona. Verdad de
  referencia: mismo identificador de Wikidata. Al mirar los primeros resultados apareció que
  `instance|a|physicist` estaba en 54 de 178 contextos y emparejaba a todos con todos; de ahí el
  filtro `taut_df`.
- **Métricas y por qué cada una.**

| Métrica | Por qué se añadió |
|---|---|
| vínculo entre fuentes, con desglose por tipo de par | es la pregunta del régimen; el desglose separa pronombres de etiquetas |
| vínculo intra-contexto | comprobar si pronombre y nombre se vinculan dentro de un texto |
| ranking (MRR, hit@1, hit@3) | con 1 promoción en 77, la métrica binaria no distinguía «sin señal» de «señal bajo el umbral». El ranking mide la señal aunque nada pase el umbral. Se calcula sobre todas las consultas; las que no tienen candidato aportan 0 y se cuentan en `unranked` |
| fusiones falsas | el error más caro: vincular a dos personas distintas |
| QA con salto | comprobar que un vínculo sirve para algo: alcanzar desde Simple un hecho declarado solo en inglés |
| basura plantada vs real | control negativo, con 50 ocurrencias reales como contraste |
| declaraciones por ocurrencia, configuraciones compartidas por par correcto | variables intermedias para saber si el límite es la capa de declaraciones |
| 10 fallos con sus configuraciones | cada informe lista casos concretos; de ahí salió que los objetos se escriben distinto en cada fuente |

### 5.5 Descompositores `heuristic`, `llm`, `both`

- **Hipótesis.** El informe de fallos mostraba 1 a 4 configuraciones por ocurrencia. Si el límite es
  la cantidad de declaraciones, un descompositor mejor debe subir las métricas sin cambiar nada más.
- **Cómo.** Misma evaluación, mismo régimen, mismos parámetros; solo cambia el origen de las
  declaraciones. Las del LLM se generan una vez (`decompose_batch`, 178 chunks) y quedan cacheadas en
  el corpus, de modo que la evaluación es offline y repetible. `both` es la unión sin duplicados.
- **Qué se comparó.** Las mismas métricas de 5.4 en una tabla de tres columnas, más el coste.

### 5.6 KB curada del repositorio original (`eval_matrix_kb`)

- **Por qué.** Las evaluaciones anteriores usan identidad de artículo como verdad, que solo cubre a
  la persona del artículo. El repositorio de Matrix tiene una KB de 10 artículos con 70 pares de alias
  escritos por una persona leyendo el texto, incluidos alias entre contextos. Es una verdad de
  referencia que no construimos nosotros y sobre declaraciones que tampoco extrajimos nosotros.
- **Cómo.** Se leen las propuestas (`proposals/*.jsonl`) y `aliases.yaml` sin copiarlos ni
  modificarlos. Cada propuesta se convierte en una `Declaration`; la capa corre sin ver los alias. Oro
  = pares de ocurrencias con el mismo `canonical`, separados en intra-contexto y entre contextos.
- **Diagnóstico previo.** Antes de mirar aciertos se cuenta, para cada par de oro, cuántas
  configuraciones comparte, con y sin filtros. Sirve para saber si el resultado puede ser distinto de
  cero: un par con menos de 3 configuraciones compartidas no puede llegar al umbral.
- **Tres configuraciones.** A: parámetros por defecto. B: `min_contexts=1`, porque con un contexto por
  artículo la corroboración entre contextos elimina toda configuración de un alias intra-contexto.
  C: además `taut_df=1.0`, porque con 10 contextos el filtro descarta lo que aparezca en más de 3. No
  se tocó ningún umbral de intensidad. Se reportan las tres.
- **Hallazgos sobre los parámetros.** `min_contexts=2` hace imposibles las propuestas dentro de un
  contexto. `taut_df` como fracción descarta todo cuando hay un solo contexto.

## 6. Cómo diseñar una prueba

### 6.1 Procedimiento

1. **Escribir la pregunta en una frase** y qué decisión depende de la respuesta. Si ninguna decisión
   depende de ella, no hace falta la prueba.
2. **Identificar la capa y su papel.** ¿Signos, declaraciones, propuestas, consulta, o el circuito
   con un intérprete? Una capa que propone se mide como proponente (cobertura, posición del correcto,
   falsos con puntaje alto); una que decide, por sus decisiones.
3. **Elegir la verdad de referencia** fuera de la cadena: por construcción, de una fuente externa, o
   escrita por una persona. Anotar qué cubre y qué no.
4. **Comprobar que la prueba puede pasar.** Antes de medir aciertos, medir la condición necesaria.
   Para la capa de propuestas: histograma de configuraciones compartidas por par de oro. Si ningún par
   llega a 3, el resultado será cero y la prueba mide la capa de declaraciones, no la regla.
5. **Definir los controles.** Un positivo donde el resultado correcto es alcanzable y un negativo que
   no debe producir nada.
6. **Fijar parámetros y umbrales de aceptación antes de correr.** Si un parámetro es la variable,
   listar las configuraciones de antemano.
7. **Elegir las métricas**: una principal, las intermedias que localizan el fallo, el coste, y una
   lista de casos concretos de acierto y de fallo.
8. **Decidir el nivel.** Si corre en segundos y tiene respuesta exacta, va a `pytest`. Si mide sobre
   un corpus, va a `experiments/` con un test de humo con `--limit`.
9. **Asegurar repetibilidad**: semilla, orden fijo, LLM cacheado, sin red.
10. **Correr con tope**, una corrida por comando, con `timeout` y métricas parciales.
11. **Escribir el informe** con lo que salió, las diferencias explicadas y los casos concretos.
12. **Convertir cada defecto encontrado en un test unitario** con la entrada que lo produjo.

### 6.2 Errores que ya se cometieron aquí

| Error | Cómo se notó | Regla que dejó |
|---|---|---|
| medir «recuperación con procedencia» como prueba de conocimiento | el primer puente pasaba sus propias métricas y era un grafo de co-ocurrencia | la verdad de referencia va fuera de la cadena |
| una métrica binaria con casi todo en cero | 1/77 no distinguía señal de ausencia de señal | añadir una métrica graduada (ranking) |
| ranking solo sobre pares con puntaje alto | MRR 1.0 con 1 consulta rankeada | calcular sobre todas las consultas y contar las que no tienen candidato |
| partir un texto para fabricar contextos | 0.0 entre secciones y una fusión falsa | contextos independientes = fuentes independientes |
| un rasgo compartido por casi todos | todos emparejados por `physicist` | revisar las configuraciones más frecuentes antes de medir |
| filtros pensados para muchos contextos usados con pocos | 20 de 1 118 configuraciones; 0 con un contexto | comprobar los filtros en el tamaño real de los datos |
| evaluar la capa estadística como si decidiera sola | «recupera 0 de 70 alias» comparaba contar con leer | medir cada componente por su papel |
| tres evaluaciones encadenadas sin tope | tres caídas por memoria | `capped.sh`, una corrida por comando |
| estructura p×p sobre todo el corpus | 7.9 GB con 4 427 variables | ninguna estructura cuadrática en el número de ocurrencias |
| datos de una corrida solo en `/tmp` | se perdieron al reiniciar | las cifras van al informe versionado |

### 6.3 Plantilla

```markdown
## Prueba: <nombre>
- Pregunta:
- Decisión que depende de la respuesta:
- Capa y papel (propone / decide):
- Datos (ruta, tamaño, cómo se generan, licencia):
- Verdad de referencia (origen, qué cubre, qué no):
- Condición necesaria y cómo se mide antes:
- Control positivo:
- Control negativo:
- Parámetros (fijos) y variable del experimento:
- Métrica principal:
- Métricas intermedias:
- Coste esperado (memoria, tiempo) y tope:
- Criterio de aceptación, fijado antes de correr:
- Nivel (pytest / humo / evaluación) y comando:
- Informe: ruta, casos concretos a listar
```

### 6.4 Ejemplo: la plantilla aplicada a una prueba pendiente

```markdown
## Prueba: revisión de propuestas por un intérprete
- Pregunta: ¿cuántos de los 70 alias de la KB de Matrix aprueba un intérprete que lee las propuestas
  ordenadas, y cuántas propuestas tiene que leer por alias correcto?
- Decisión: si la cola ordenada reduce el trabajo de revisión frente a leer el texto sin cola.
- Capa y papel: circuito completo; el intérprete decide, la capa estadística ordena.
- Datos: Matrix/examples/kb_wikipedia_10_articles (solo lectura), 699 propuestas.
- Verdad de referencia: aliases.yaml. No cubre 2 alias cuyo signo no fue extraído.
- Condición necesaria: cada consulta debe tener candidatos; hoy 11 de 41 con min_contexts=1,
  taut_df=1.0. Medir antes cuántos alias son alcanzables.
- Control positivo: corpus sintético Curie/Franklin.
- Control negativo: pares de personas distintas ofrecidos al intérprete; deben rechazarse.
- Parámetros: los de la corrida C. Variable: con cola / sin cola; LLM / persona.
- Métrica principal: alias aprobados correctos e incorrectos.
- Intermedias: propuestas leídas por alias correcto; posición del correcto en la cola.
- Coste: una llamada por propuesta; respuestas cacheadas en JSONL; tope 4 GB.
- Aceptación: fijar antes de correr.
- Nivel: evaluación + humo con FakeBackend.
- Informe: .herdr/<nombre>_report.md con todos los rechazos y aprobaciones erróneas.
```

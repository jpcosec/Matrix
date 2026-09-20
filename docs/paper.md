# Convergencia de configuraciones: poblar mundos lógicos desde texto sin catálogo global de símbolos

**Documento técnico para publicación.** Estado del repositorio: `main` en `da21ea3` (2026-09-20).
Todo número citado aquí sale de una corrida reproducible (§13) y de los informes por etapa en
`.herdr/*_report.md`. Donde un resultado es malo, se reporta malo: ningún umbral se ajustó para
mejorar una métrica.

---

## Resumen

Presentamos un sistema que puebla una base de conocimiento lógica desde texto crudo y permite
consultarla conversando, al estilo de SHRDLU, con cada respuesta anclada a la cita que la sostiene.
El motor lógico es **Matrix**, una lectura operacional del *Tractatus* de Wittgenstein: el mundo es
la totalidad de los hechos, la unidad es la configuración `(R a b)`, y la forma lógica de cada juego
de lenguaje es estructural, nunca estadística. La contribución central es un algoritmo de
**convergencia de configuraciones** que reemplaza tres pasos clásicos del procesamiento de texto
(normalización de entidades, resolución de correferencia y filtrado de ruido) por un único
principio: un símbolo es el par *(signo, contexto de declaración)*, y dos símbolos de contextos
distintos son el mismo referente cuando las configuraciones en que entran se incluyen
estadísticamente una en otra. La inclusión se mide con la intensidad de implicación del Análisis
Estadístico Implicativo (SIA/CHIC), que aquí no produce hechos ni sentido: solo mide convergencia.

Evaluamos sobre un corpus sintético con referentes conocidos y sobre un corpus real de 89 físicos
(Simple English Wikipedia, Wikipedia en inglés, Wikidata y GAP). En el sintético la taxonomía de
contextos tiene pureza 100 %, el pronombre `she` converge con el nombre propio en 15 de 15
artículos y los 10 hechos falsos plantados quedan aislados. En texto real el resultado es sobrio:
con un descompositor heurístico converge 1 de 77 personas entre fuentes; con un LLM pequeño usado
como descompositor de superficie convergen 5 de 79 y el rango recíproco medio pasa de 0.055 a
0.265, con cero fusiones falsas. Derivamos una **ley de soporte mínimo** que explica esos números
de forma cuantitativa: con inclusión perfecta la intensidad depende solo del número de
configuraciones del símbolo, y el umbral de promoción exige al menos tres configuraciones
informativas compartidas, mientras que la mediana real es una declaración por símbolo. El cuello de
botella no es la regla de convergencia sino la capa de declaraciones.

Documentamos además un fallo de ingeniería con valor general. La primera implementación comparaba
todos los símbolos contra todos en matrices densas: 7.9 GB con 4 427 símbolos y muerte por falta de
memoria con 5 701. El rediseño **aglomerativo**, que calcula la intensidad solo sobre pares
candidatos obtenidos de un índice invertido e ingiere los contextos por lotes, baja el pico a
250 MB y el tiempo de 245 s a 10 s con resultados equivalentes. La versión cuadrática no era solo
cara: contradecía el modelo.

---

## 1. Introducción

### 1.1 El problema

Las bases de conocimiento extraídas de texto heredan casi siempre la misma arquitectura: un
extractor produce tripletas, un normalizador pliega las menciones a un catálogo global de
entidades, un módulo de correferencia resuelve pronombres, y un filtro estadístico descarta lo que
parece ruido. Cada paso toma decisiones irreversibles antes de que exista evidencia para tomarlas.
Plegar `Curie` a una entidad global decide, en la entrada, que Marie y Pierre son o no son la misma
cadena. Resolver `she` en el momento de leerlo decide el referente con la información de una sola
oración. Y el filtro de ruido trata la ausencia de co-ocurrencia como si fuera una afirmación.

Matrix propone otra cosa. Su tesis, tomada del *Tractatus*, es que el significado de un signo es su
uso dentro de un juego de lenguaje, y que lo que tiene sentido o no lo tiene está fijado por la
forma lógica del juego, no por la frecuencia con que algo se dijo. De ahí se sigue una consecuencia
de diseño que organiza todo este trabajo: **no hay que desambiguar antes de poblar; la
desambiguación es lo que ocurre cuando muchos contextos hablan del mismo campo**.

### 1.2 La tesis

> Un símbolo es el par *(signo, contexto de declaración)*. `she` en un artículo sobre Marie Curie es
> un símbolo legítimo de ese contexto, tan válido como `marie_curie`. La identidad entre símbolos de
> contextos distintos no se decide por coincidencia de cadenas ni por un catálogo: se *propone*
> cuando las configuraciones en que entra uno están incluidas en las del otro, y se *promueve* por
> una regla de convergencia o por curado humano. Un hecho espurio no encuentra configuraciones
> compatibles en otros contextos y queda aislado. La calidad de la base sube con el volumen.

### 1.3 Contribuciones

1. **Un modelo de símbolo contextual** `signo@contexto` sin catálogo global ni plegado de alias, con
   procedencia exacta por hecho (documento, desplazamiento, extractor, nivel epistémico).
2. **El algoritmo de convergencia de configuraciones**, que usa la intensidad de implicación de SIA
   sobre la matriz *configuraciones × símbolos*, con filtros de corroboración y de tautología, una
   regla de promoción direccional y un punto fijo iterativo sobre los referentes ya convergidos.
3. **Una delimitación estricta del papel de la estadística**: CHIC mide convergencia en exactamente
   tres lugares (taxonomía de contextos, convergencia de símbolos, mantenimiento de cada juego) y en
   ninguno produce hechos, sentido ni relaciones.
4. **Una ley de soporte mínimo** que liga el umbral de promoción con el número de configuraciones
   por símbolo y predice los valores de intensidad observados.
5. **Un rediseño aglomerativo** con memoria acotada por el número de declaraciones, junto con el
   registro honesto del fallo que lo motivó y una barrera operativa contra procesos desbocados.
6. **Un protocolo de evaluación** con cuatro regímenes, tres descompositores, verdad de referencia
   externa (Wikidata, identidad de artículo) y métricas que separan la señal del algoritmo de la
   calidad de la extracción.

---

## 2. Antecedentes

### 2.1 Matrix: el *Tractatus* como motor booleano

Matrix representa el conocimiento como una colección de **juegos de lenguaje** (`WiGame`). Cada
juego está indexado por un contexto y una relación, `WiGame(ctx, R)`, y mantiene dos matrices sobre
sus ejes de símbolos:

- **`S_i`, la forma lógica.** Dice qué combinaciones tienen sentido en el juego. Sus valores son
  `sinnvoll` (con sentido), `sinnlos` (tautológico o vacío) y `unsinnig` (absurdo). Es *a priori*
  respecto de los hechos del juego: emerge de la firma de la relación y del cruce de contextos
  cerrados. Nunca se estima por frecuencias. Que dos signos no co-ocurran no vuelve absurda su
  combinación; el silencio no es un sinsentido.
- **`V_i`, los valores de verdad.** Tres valores: `TRUE`, `FALSE`, `UNKNOWN`. `UNKNOWN` es un
  ciudadano de primera clase: es lo que responde el sistema cuando nadie ha afirmado algo.

La deducción es álgebra booleana: una matriz de implicación `I` cuya clausura se obtiene por
elevación al cuadrado repetida, y proyecciones de enrutamiento (`RoutingProjection`) que transportan
una consulta de un juego a otro. Cada hecho lleva un registro de evidencia con su procedencia
`Prov(f) = (documento, desplazamiento, confianza, extractor)`, un nivel epistémico
(`observed > confirmed > inferred > statistical`) y su estado de curado. El motor se incorporó al
repositorio como *subtree* y se extendió con los verbos necesarios (§6.2).

### 2.2 SHRDLU: el modelo de interacción

De SHRDLU (Winograd, 1971) no tomamos el mundo de bloques ni el planificador con retroceso, sino el
**bucle de conversación**: afirmar, preguntar, pedir una justificación (`why`), recibir una pregunta
de aclaración cuando la frase es ambigua, y definir conceptos nuevos hablando. El planificador de
Micro-Planner se sustituye por el punto fijo booleano del núcleo. El modelo de lenguaje, cuando
interviene, analiza y verbaliza; no decide la verdad de nada.

### 2.3 SIA/CHIC: la intensidad de implicación

El Análisis Estadístico Implicativo (Gras et al., *Statistical Implicative Analysis*, Springer SCI
127, 2008) mide cuán sorprendente es que una regla `a → b` tenga tan pocos contraejemplos. Sobre `n`
individuos, con `n_a` y `n_b` los que verifican cada variable y `n_{a∧¬b}` los contraejemplos:

- El número esperado de contraejemplos bajo independencia es `λ = n_a · n_{¬b} / n`.
- El índice es `q(a,¬b) = (n_{a∧¬b} − λ) / √λ`.
- La **intensidad clásica** es `ϕ(a,b) = 1 − Pr[Q ≤ q]`. Se calcula con la Poisson exacta cuando
  `λ ≤ 4`, que es el caso habitual en texto, y con la aproximación normal en otro caso. Vale 0
  cuando `n_b = n`.
- La **versión entrópica** pondera por un índice de inclusión `τ` construido con las entropías
  condicionales `H(b|a)` y `H(¬a|¬b)` con exponente `α = 2`, y define `φ = (ϕ · τ)^{1/2}`.
- La **cohesión** de un par es `c = (1 − H(ϕ)²)^{1/2}` si `ϕ > 0.5`, y sobre ella se construye una
  jerarquía implicativa aglomerativa cuyos **niveles significativos** son los máximos locales de un
  estadístico de concordancia.

Implementamos todo esto en el paquete `sia/`, verificado contra los ejemplos numéricos del libro
(Tabla 1, p. 22: `τ = 0.6035`, `φ = 0.777` con tolerancia de una milésima). La propiedad que nos
importa es la **direccionalidad**: `ϕ(a,b)` alto y `ϕ(b,a)` bajo significa que todo lo que se dice
de `a` se dice de `b`, pero no al revés. Esa asimetría es exactamente la forma de una proyección
entre un símbolo pobre, como un pronombre, y uno rico, como un nombre propio.

### 2.4 Korel: la capa de signos

De Korel (un sistema de recuperación en Go) tomamos solo las tres primeras fases de su cadena:
extracción, tokenización con lista de paradas, y agrupación voraz de términos de varios tokens. No
tomamos su etiquetado taxonómico, su índice ni su recuperación. En nuestro sistema esta capa no
produce símbolos globales, hechos ni sentido: produce **contextos observables de uso**, los signos
tal como aparecen, y sus desplazamientos en el texto.

---

## 3. Modelo

### 3.1 Contextos y signos

Un **contexto de declaración** es un trozo de texto (`Chunk`) con identificador propio: un documento
completo (`Q7186`) o una sección (`Q7186#2`; el encabezado de un artículo es `#0`). Cada contexto
tiene su inventario de **signos locales** (`LocalSign`), de tres clases:

- `name`: ventanas de tokens con mayúscula inicial, que admiten conectores internos (`University of
  Paris`, `Jacobus Henricus van 't Hoff`) y no cruzan puntuación;
- `pronoun`: `she`, `he`, `it`, `they` y sus equivalentes. Siempre son signos, nunca se resuelven;
- `term`: sustantivos y términos de varios tokens.

Cada signo conserva sus apariciones con desplazamiento de carácter. Un índice signo → contextos
(`SignIndex`) existe, pero **solo para enrutar** una pregunta hacia los contextos donde un signo
aparece. Nunca se usa para declarar identidad.

### 3.2 Símbolos

> **Definición 1 (símbolo).** Un símbolo es el par `(norm(signo), ctx)`, escrito `signo@ctx`.

`she@Q7186` y `she@Q7259` son dos símbolos distintos. `curie@Q7186` y `curie@Q37463` también: uno
vive en el artículo de Marie y el otro en el de Pierre, y es el uso, no la cadena, lo que decidirá
si se proyectan. La normalización se limita a minúsculas y separadores; sirve como *evidencia
superficial* en la primera pasada del algoritmo y nada más.

### 3.3 Declaraciones y configuraciones

Un **descompositor** lee cada oración dentro de su contexto y emite declaraciones
`(R a b)@ctx`, donde `a` y `b` son símbolos de ese mismo contexto y `R` pertenece a un conjunto
cerrado de familias (`instance`, `has_property`, `born_in`, `died_in`, `citizen_of`, `field`,
`award`, `educated_at`, `employer`, entre otras) o es una relación abierta `rel:<verbo>`. El
descompositor no asigna verdad ni resuelve referencias: propone forma.

Cada declaración se ingiere como un hecho `observed` y `confirmed` **del juego de su contexto**,
`WiGame(ctx, R)`. Lo que un artículo afirma es verdadero *en el juego de ese artículo*. Su alcance
fuera de él es lo que la convergencia tiene que ganar.

> **Definición 2 (configuración).** Dada una declaración `(R a b)@ctx`, el símbolo `a` entra en la
> configuración `R|a|ref(b)` y el símbolo `b` en `R|b|ref(a)`, donde `ref(x)` es el referente ya
> convergido de `x` si existe, y en su defecto su forma normalizada.

Una configuración es entonces «ocupar el papel *rol* de la relación *R* frente a tal
co-participante». `born_in|a|warsaw` es la configuración de todo símbolo del que se dice que nació
en Varsovia. La dependencia de `ref(·)` hace al algoritmo iterativo: cuando dos co-participantes
convergen, configuraciones que antes eran distintas pasan a ser la misma.

### 3.4 Qué aporta cada pieza

| Pieza | Aporta | No aporta |
|---|---|---|
| Capa de signos (Korel) | contextos, signos locales, desplazamientos, índice de enrutamiento | símbolos globales, hechos, sentido |
| Descompositor (heurística o LLM) | candidatos `(R a b)` por oración con signos locales | decisiones lógicas, resolución de pronombres |
| Motor Matrix | juegos por `(contexto, R)`, sentido, verdad trivaluada, deducción, proyecciones, procedencia y curado | estadística |
| SIA/CHIC | medida de convergencia en tres matrices (§5.6) | hechos, sentido, relaciones, identidad |

---

## 4. El primer puente, y por qué estaba mal

Conviene contar el error, porque es el error natural. La primera versión del puente entre texto y
motor (commits hasta `d4cc05c`) construía una matriz *oraciones × conceptos*, corría CHIC sobre ella
e introducía los arcos del grafo implicativo en `V_i` bajo una relación ficticia `implies`. Además
derivaba candidatos a `unsinnig` de los pares de conceptos que nunca co-ocurrían, plegaba alias a la
entrada y deduplicaba entre contextos. La métrica de éxito era «recuperación con procedencia».

Eso es, con otro nombre, un grafo de conocimiento por co-ocurrencia, que es precisamente lo que
Matrix rechaza. Confunde tres planos que el *Tractatus* separa: lo que **se dijo** (hechos de un
juego), lo que **puede decirse** (forma lógica), y lo que **suele decirse junto** (frecuencia). Una
regularidad estadística no es un hecho ni una regla de sentido, y que algo no se haya dicho no lo
vuelve absurdo.

La corrección, escrita en `specs/convergence.md`, reduce la estadística a un único papel: **medir
cuánto convergen los usos**. Todo lo demás del primer puente se eliminó del código (`da21ea3`).

---

## 5. El algoritmo de convergencia

### 5.1 La matriz

Sea `V` el conjunto de **variables**: los símbolos con al menos `min_support = 2` declaraciones. Sea
`K` el conjunto de configuraciones informativas (§5.2). La matriz binaria `X ∈ {0,1}^{|K|×|V|}`
tiene `X[k,s] = 1` cuando el símbolo `s` entra en la configuración `k`. Las configuraciones son los
individuos y los símbolos son las variables: es la disposición inversa a la intuitiva, y es la que
hace que `s → t` signifique *«toda configuración de `s` es también configuración de `t`»*.

### 5.2 Dos filtros, ambos principios del modelo

- **Corroboración (`min_contexts = 2`).** Una configuración declarada en un solo contexto no aporta
  evidencia de identidad entre contextos y se descarta antes de medir. Este filtro es el que hace
  operativo el principio «la basura se aísla»: un hecho plantado, `born_in|a|tokyo_7`, aparece en un
  contexto y desaparece de la matriz. Sin él, un único contraejemplo espurio hunde la inclusión: en
  el corpus sintético la convergencia de `she` cae de 15/15 a 10/15.
- **Tautología (`taut_df = 0.30`).** Una configuración que aparece en más del 30 % de los contextos
  es *sinnlos* respecto del corpus: es verdadera para casi todos y no discrimina a nadie. En el
  corpus de físicos la única descartada es `instance|a|physicist`, presente en 54 de 178 contextos.
  Ser físico no identifica a ningún físico.

### 5.3 Intensidad sobre pares candidatos

No se calcula la intensidad entre todos los pares de símbolos (§7). Un índice invertido
configuración → símbolos genera los **pares candidatos**: pares ordenados `(s,t)` que comparten al
menos una configuración, con `n_st` el número de configuraciones compartidas. Para cada candidato
se arma la contingencia `(n, n_s, n_t, n_st, n_{s∧¬t})` en arreglos de una dimensión y se evalúa
`ϕ(s,t)` con el mismo núcleo numérico que la versión densa (igualdad verificada con tolerancia
`1e-9`). La medida por defecto es la **clásica**: en texto real `λ` es pequeño y el índice
entrópico castiga cada contraejemplo con demasiada fuerza, mientras que la clásica es exactamente
el modelo de Poisson del libro.

### 5.4 Regla de promoción

Para un candidato `(s,t)` con `ϕ(s,t) ≥ φ_min = 0.90`:

1. Si `ϕ(t,s) ≥ 0.90` también, el par es candidato a **`equivalent`**: mismo referente. Se promueve
   automáticamente cuando `min(ϕ(s,t), ϕ(t,s)) ≥ 0.95`, comparten **al menos 2 configuraciones
   informativas** y esas configuraciones provienen de al menos 2 contextos. Si `s` y `t` viven en el
   mismo contexto, que es la correferencia clásica entre `she@ctx` y `marie_curie@ctx`, basta con las
   2 configuraciones compartidas.
2. Si solo un sentido supera el umbral, el par es candidato a **`projection`** direccional `s → t`,
   por cada relación que ambos comparten, y solo entre contextos distintos. Se promueve con
   `ϕ(s,t) ≥ 0.95` y las mismas guardas.
3. Todo lo demás queda como `proposed` en la cola de curado, con sus configuraciones compartidas y
   las oraciones citadas, para que un humano o un LLM asistente lo confirme o lo rechace.

Los candidatos se procesan en orden `(−ϕ, s, t)` para que el resultado sea determinista. Los
referentes se guardan como particiones en la memoria del mundo (`system.referents`,
`system.equivalences`), no como un juego de equivalencias con una matriz símbolos × símbolos.

### 5.5 Punto fijo

Tras cada pasada, los símbolos promovidos a `equivalent` reciben un identificador de referente
`ref:k`. En la pasada siguiente, `ref(·)` sustituye la forma superficial por ese identificador al
construir las configuraciones (Definición 2), de modo que `employer|a|cambridge` y
`employer|a|university_of_cambridge` se vuelven una sola configuración si sus objetos convergieron.
El proceso se repite hasta que una pasada no promueve nada o se alcanza `max_iter = 5`. Es
idempotente: una segunda corrida sobre el mismo mundo no promueve nada nuevo.

```
CONVERGER(mundo, contextos, declaraciones):
  V        ← símbolos con ≥ min_support declaraciones
  repetir hasta max_iter:
      K    ← configuraciones(declaraciones, ref)         # Definición 2
      K    ← K sin las de < min_contexts ni las de df > taut_df
      P    ← pares candidatos por índice invertido K → V  # n_st ≥ min_support
      ϕ    ← intensidad clásica sobre P                   # arreglos 1-D
      para (s,t) en P ordenado por (−ϕ, s, t) con ϕ(s,t) ≥ 0.90:
          si ϕ(t,s) ≥ 0.90: proponer equivalent; promover si ambas ≥ 0.95 y n_st ≥ 2
          si no:            proponer projection s→t; promover si ϕ(s,t) ≥ 0.95 y n_st ≥ 2
      actualizar ref(·) con los equivalent promovidos
      si no hubo promociones: terminar
```

### 5.6 Los tres usos de CHIC, y solo tres

| Uso | Individuos | Variables | Qué produce |
|---|---|---|---|
| **Taxonomía de contextos** | contextos | signos y configuraciones `(R · b)` declaradas | `A → B` significa «donde se dice A se dice B»: anidamiento con dirección. La jerarquía, cortada en sus niveles significativos más las clases maximales, es el árbol de contextos y sus rutas |
| **Convergencia de símbolos** | configuraciones | símbolos `signo@ctx` | proyecciones direccionales, equivalencias y, por jerarquía, una taxonomía de referentes |
| **Mantenimiento de cada juego** | sujetos del juego | coordenadas `(R, b)` | columnas tautológicas en un subconjunto → compuertas `C_k`; colisiones de `W ⊗ Wᵀ − I` → coordenadas discriminantes `D_i`; subjuegos |

En el corpus de vegetales, que es el ejemplo de referencia del paper de Matrix, el mantenimiento
propone `verde` como compuerta del juego de lechugas y separa la colisión `lechuga`/`espinaca` con el
discriminante `hoja_lisa`/`hoja_rugosa`. Cuando esas dos coordenadas faltan, reporta la colisión
como no resuelta en lugar de inventar un discriminante.

### 5.7 Convergencia aglomerativa por lotes

Los contextos entran al mundo en lotes de 40, ordenados por documento y sección. Cada lote se suma
al índice invertido, y el informe de convergencia (referentes, puntajes, pares ya procesados) se
arrastra de un lote al siguiente, de modo que el mundo crece en lugar de recalcularse. Es el
mantenimiento de `W_i` que el modelo prescribe. El resultado por lotes reproduce las particiones de
referentes de la corrida completa (test con lotes de 5 sobre el corpus sintético). Una limitación
declarada: la implementación actual vuelve a puntuar la lista acumulada de candidatos en cada lote y
omite los pares ya procesados. Puntuar solo los pares que tocan al lote nuevo es una optimización
pendiente que no cambia el resultado.

### 5.8 La ley de soporte mínimo

El umbral de promoción tiene una lectura exacta. Supongamos la mejor situación posible para un par:
inclusión perfecta, `n_{s∧¬t} = 0`. Entonces:

- si `λ ≤ 4`: `ϕ = 1 − e^{−λ}`;
- si `λ > 4`: `ϕ = Φ(√λ)`, con `Φ` la distribución normal estándar.

Y como `λ = n_s · n_{¬t} / n` con `n` grande (miles de configuraciones) y `n_t` pequeño, se tiene
`λ ≈ n_s`: **la intensidad máxima alcanzable depende solo del número de configuraciones
informativas del símbolo**.

| configuraciones de `s`, todas compartidas | 1 | 2 | 3 | 4 | 5 | 7 | 9 |
|---|---|---|---|---|---|---|---|
| `ϕ` máxima teórica | 0.632 | 0.865 | 0.950 | 0.982 | 0.987 | 0.996 | 0.999 |

Los valores medidos calzan: los pares con 4 configuraciones compartidas dan `ϕ` entre 0.9803 y
0.9815, los de 5 dan 0.9864 y 0.9865, el de 7 da 0.9921 y el de 9 da 0.9976 (algo por debajo del
máximo porque `n_{¬t}/n < 1`). La consecuencia es directa: **proponer exige al menos 3
configuraciones informativas compartidas sin contraejemplos, y con 1 o 2 la intensidad no puede
pasar de 0.87 por muy idénticos que sean los usos**. El corpus sintético necesitó unas 8
configuraciones por símbolo para superar con holgura el umbral. En el corpus real la mediana es
**una** declaración por símbolo. Esa diferencia, y no un defecto de la regla, explica los resultados
de §9.

---

## 6. Sistema

### 6.1 Flujo

```
texto ─► capa de signos: chunks (contextos), signos locales, offsets, índice
              │
              ▼
      descompositor por oración ─► (R a b)@ctx candidatas, con Prov
              │
              ▼
      Matrix: WiGame(ctx, R) ─► sentido ─► V_i por contexto (observed, confirmed)
              │
              ▼
      CHIC: contextos × declaraciones   ─► árbol de contextos
            configuraciones × símbolos  ─► projection / equivalent
            sujetos × coordenadas       ─► compuertas, subjuegos, D_i
              │
              ▼
      promoción por convergencia o curado ─► consultas ruteadas con cita
```

### 6.2 Módulos

| Paquete | Contenido |
|---|---|
| `populator/` | lectura de documentos, `chunk_documents(unit="document"\|"section")`, signos locales con desplazamientos, índice de enrutamiento |
| `pipeline/decompose.py` | descompositor heurístico (cópula, nacimiento y muerte con fecha y lugar, premios con variante canónica, empleador, relaciones abiertas solo con verbo plausible) y descompositor LLM por chunk |
| `pipeline/llm_cache.py`, `decompose_batch.py` | caché versionada de declaraciones LLM, con clave `sha1` del texto del chunk |
| `pipeline/ingest.py` | ingesta aditiva por contexto y `build_world` por lotes |
| `pipeline/convergence.py` | taxonomía de contextos, convergencia de símbolos, mantenimiento de juegos |
| `pipeline/query.py` | `ask`: consulta ruteada que sigue proyecciones promovidas y grupos de referentes hasta `hops` saltos y devuelve hechos, ruta y cita |
| `pipeline/curate.py` | cola de curado asistida por LLM sobre candidatos `projection` y `equivalent` |
| `sia/` | contingencia densa y por pares, intensidad clásica y entrópica, cohesión, jerarquía, niveles significativos, similitud de Lerman, AROMA |
| `matrix/` | motor booleano y runtime de expresiones S: `check`, `assert`, `ingest`, `create (symbol\|relation\|li\|wigame\|context)`, `candidate`, `promote`, `reject`, `retract`, `why`, `define`, `project`, `return` |
| `matrix/prototypes/shrdlu/` | REPL en español e inglés controlado |

### 6.3 El LLM como descompositor de superficie

El paper de Matrix propone usar modelos pequeños como descompositores que no toman decisiones
lógicas. Lo implementamos así: **una llamada por chunk** con el título, las oraciones numeradas, la
lista cerrada de signos locales y las familias de relación. El modelo debe devolver un arreglo JSON
de tripletas que usen **solo** signos de la lista. Los pronombres son signos válidos y no se
resuelven. No puede inventar relaciones fuera de las familias salvo `rel:<verbo>`, y debe preferir
el signo más largo disponible como objeto. La validación es estricta: toda tripleta con un signo
ajeno al contexto o una relación no permitida se descarta. El modelo no puede crear símbolos, no
decide identidad y no asigna verdad. Las declaraciones quedan en una caché versionada dentro del
corpus, de modo que la evaluación corre sin red y es reproducible bit a bit.

Coste medido: 178 chunks con `deepseek-flash` sin razonamiento extendido, unos 30 s por chunk, unos
11 minutos con 8 trabajadores, una sola vez. Produce 11 242 declaraciones (media 62.9 y mediana 46.5
por chunk) frente a 2 931 de la heurística.

### 6.4 Conversar con el mundo

```
> was Curie born in Warsaw?
Sí: (born_in curie@Q7186 warsaw@Q7186) [corpus/physicists/en/Q7186.md:938-962]
    · ruta: wigame:Q7186:born_in
> why?
porque (born_in curie@Q7186 warsaw@Q7186) [observed; corpus/physicists/en/Q7186.md:938-962]

> was she born in Warsaw?            (sobre los 20 primeros artículos de Simple English)
No lo sé (nadie lo ha confirmado).
```

La segunda respuesta es el comportamiento correcto y no un defecto de interfaz. En ese régimen el
hecho lo declara `maria_salomea_skodowska@Q7186`, y `she@Q7186` no converge con ese símbolo porque no
comparten suficientes configuraciones. El sistema no adivina: responde `UNKNOWN`. La precisión de las
respuestas ruteadas es 1.0 en todos los regímenes; lo que falta es cobertura.

---

## 7. Una lección de ingeniería: de símbolos × símbolos a aglomerativo

### 7.1 El fallo

La primera implementación de la convergencia hacía lo obvio: construir `X`, calcular `XᵀX` y
evaluar la intensidad sobre la matriz completa de `p × p` símbolos. Un análisis de su memoria
muestra por qué no podía escalar:

- la contingencia densa materializa tres matrices `p × p` en coma flotante de 64 bits;
- la intensidad clásica crea además `λ`, `q`, la cola normal, la acumulada de Poisson y varias
  copias intermedias, todas `p × p`; la entrópica añade ocho más;
- un diccionario de Python guardaba los contextos compartidos de **cada par** de símbolos;
- dos bucles anidados en Python recorrían los `p²` pares;
- la métrica de ranking de la evaluación volvía a construir todo por su cuenta.

Con el descompositor heurístico hay 690 variables y nada de esto se nota. Con el LLM hay 4 427:
19.6 millones de pares, 157 MB por matriz, más de diez matrices vivas a la vez. El pico medido fue
de 7.9 GB y 237 s solo en convergencia. Con los dos descompositores combinados hay 5 701 variables,
y el proceso murió con 11 GB residentes. El 20 de septiembre de 2026 ese proceso, lanzado tres veces
sin límite de memoria desde agentes auxiliares, hizo que el sistema operativo matara el grupo de
procesos completo de la terminal, con todos los agentes dentro.

### 7.2 Por qué era un error de modelo y no solo de tamaño

Comparar cada símbolo del corpus contra todos los demás es afirmar, en el código, que cualquier
símbolo podría ser cualquier otro. El modelo dice lo contrario: un símbolo solo puede converger con
otro si comparten alguna configuración informativa, y los mundos **crecen por aglomeración**. Un
contexto nuevo se compara contra lo que ya existe y contra los referentes ya convergidos. La matriz
densa es casi toda ceros que se pagan igual. La versión cuadrática no era una implementación
ingenua del algoritmo correcto: era una implementación fiel de un algoritmo equivocado.

### 7.3 El rediseño

1. **Pares candidatos por índice invertido.** De 19.6 millones de pares posibles se pasa a 275
   candidatos con el LLM y a 326 con ambos descompositores. El coste es la suma de los cuadrados de
   los tamaños de las configuraciones, acotado por un tamaño máximo de 500 símbolos por
   configuración; las mayores ya son tautológicas de hecho.
2. **Intensidad sobre arreglos de una dimensión**, con el mismo núcleo numérico que la versión densa,
   que se conserva para los tests contra el libro.
3. **Contextos compartidos solo para los pares que superan el umbral.**
4. **Lotes con informe arrastrado** (§5.7).
5. **Ranking sobre candidatos**: la evaluación ordena solo los pares que comparten alguna
   configuración, y las consultas sin candidato cuentan como cero.

| Descompositor | Variables | Pico antes | Pico después | Convergencia antes | Total después |
|---|---|---|---|---|---|
| heurístico | 690 | 1 488 MB | 198 MB | 2.2 s | 2.5 s |
| LLM | 4 427 | 7 921 MB | 250 MB | 237 s | 10.2 s |
| ambos | 5 701 | muerte por memoria a 11 GB | 274 MB | no terminó | 14.4 s |

Un test de escala con 3 000 símbolos en 300 contextos corre en 3.2 s con 16 MB de pico.

### 7.4 Qué cambió en los resultados

La convergencia entre fuentes se mantiene en heurístico (1 de 77) y sube en LLM de 4 a 5 de 79. Los
conteos brutos de promociones bajan (10 → 6 y 115 → 45) por cuatro razones identificadas: solo se
consideran candidatos con soporte suficiente; el orden de proceso es ahora por intensidad
decreciente; los pares no promovidos se reevalúan en pasadas posteriores en lugar de congelarse; y
las equivalencias ya no se escriben como hechos de un juego global. El número de referentes es
idéntico (3 y 18). El conteo de símbolos aislados pasa de 0 a 538 y a 3 896, y es la cifra correcta:
antes, puntajes espurios entre símbolos sin nada en común impedían que nada quedara aislado.

### 7.5 La barrera operativa

Un algoritmo bien diseñado no basta cuando quien lo ejecuta es un agente automático. Añadimos
`scripts/capped.sh`, que corre cualquier comando en un grupo de control transitorio con memoria
máxima y sin intercambio, de modo que el sistema mata **solo ese proceso**. La evaluación limita
además su propio espacio de direcciones y escribe métricas parciales tras cada etapa. Tres reglas
quedaron fijadas para todo encargo a agentes: tope de memoria en toda corrida pesada, una corrida
por comando, y ninguna estructura que crezca con el cuadrado del número de símbolos.

---

## 8. Protocolo experimental

### 8.1 Corpus sintético con referentes conocidos

Treinta artículos generados: 15 sobre Marie Curie y 15 sobre Rosalind Franklin. Cada persona tiene
24 hechos nucleares repartidos entre tres formas de sujeto (nombre completo, apellido, pronombre
`she`) más hechos variables con sujetos ajenos. Se plantan **10 hechos falsos**, uno por artículo
elegido sin reemplazo, de la forma `born_in she Tokyo_k`. La verdad de referencia es total: sabemos
qué `she` es quién y qué hechos son basura. Como la plantilla repetida *es* la señal de identidad,
estos tests desactivan el filtro de tautología.

### 8.2 Corpus real: físicos nacidos entre 1850 y 1900

- **Selección.** Consulta a Wikidata por ocupación «físico» o cualquiera de sus subclases, con
  artículo en Simple English Wikipedia: 103 personas, de las que quedan **89** tras descartar 14
  esbozos de menos de 300 caracteres.
- **Textos.** El artículo de Simple English (mediana 1 436 caracteres) y el artículo completo de la
  Wikipedia en inglés con sus secciones (1.8 MB en total, mediana de unos 16 800 caracteres,
  recortado a 40 000 en límite de sección).
- **Verdad de referencia.** 2 802 hechos de Wikidata sobre 12 relaciones (31.5 por persona),
  menciones cruzadas entre artículos (60 artículos mencionan a otro físico del corpus), y la
  identidad de artículo: dos contextos con el mismo identificador de Wikidata hablan de la misma
  persona.
- **GAP.** Las 454 filas de validación del corpus de correferencia GAP (908 pares). Su cobertura es
  0: ninguna de sus páginas trata de un físico del corpus. Se reporta tal cual.

Licencias: CC BY-SA para los textos de Wikipedia, CC0 para Wikidata.

### 8.3 Regímenes

| Régimen | Contextos | Qué pone a prueba |
|---|---|---|
| `document` sobre Simple | 89, uno por persona | línea base: no hay segunda fuente con la que converger |
| `document` sobre inglés | 89 artículos completos | lo mismo, con más texto |
| `section` sobre inglés | 564 secciones | convergencia entre secciones de un mismo artículo |
| **`pairs`** | 178: Simple más encabezado en inglés | **dos fuentes independientes por persona** |

El régimen `pairs` es el experimento que corresponde a la tesis: dos textos escritos por personas
distintas sobre el mismo referente.

### 8.4 Métricas

- **Convergencia entre fuentes.** Fracción de personas para las que algún símbolo del artículo
  Simple (`she`, `he` o la etiqueta) converge, por referente compartido o por proyección promovida
  en cualquier sentido, con algún símbolo del encabezado en inglés de la misma persona. Se desglosa
  en pronombre↔pronombre, etiqueta↔etiqueta y pronombre↔etiqueta.
- **Intra-contexto.** Fracción de contextos en que el pronombre converge con la etiqueta.
- **Ranking.** Para cada símbolo sujeto del artículo Simple, posición del símbolo correcto del otro
  contexto entre sus candidatos ordenados por intensidad. Se reportan MRR, acierto en 1 y acierto en
  3 **sobre todas las consultas**; las que no tienen candidato aportan cero. Mide la señal del
  algoritmo aunque nada se promueva.
- **Falsas fusiones.** Promociones entre símbolos de personas distintas sin mención cruzada.
- **Preguntas con Wikidata.** Cobertura y precisión de `ask` sobre los hechos de referencia,
  preguntando por etiqueta, por pronombre y **con salto**: hechos declarados solo en el contexto en
  inglés, preguntados desde el símbolo del contexto Simple.
- **Basura.** Fracción de 50 símbolos plantados que queda aislada, frente a 50 símbolos reales
  muestreados.
- **Coste.** Tiempo por etapa y memoria residente máxima.

---

## 9. Resultados

### 9.1 Corpus sintético

| Propiedad | Resultado |
|---|---|
| Pureza de la taxonomía de contextos | **100 %**: 5 nodos, ninguno mezcla Curie con Franklin; 420 aristas de anidamiento |
| `she@curie_i` converge con `marie_curie@`/`curie@` | **15 de 15** |
| `she@franklin` comparte referente con algún símbolo de Curie | **nunca** |
| `franklin@` converge consigo mismo entre artículos | 15 de 15 |
| Hechos plantados aislados | **10 de 10**, todos con puntaje 0.0 |
| Idempotencia | segunda corrida: 0 promociones |
| Iteraciones del punto fijo | 2 |

Cuando hay soporte, el algoritmo hace lo que la tesis promete: separa referentes homónimos en el
signo (`she`), resuelve la correferencia sin un módulo de correferencia, y deja fuera el ruido sin un
filtro de ruido.

### 9.2 Corpus real: regímenes

| Régimen | Contextos / símbolos | Promociones | Hallazgo |
|---|---|---|---|
| `document` Simple | 89 / 2 719 | 0 | un contexto por persona: no hay nada con qué converger |
| `document` inglés | 89 / 15 545 | 4 a 7 proyecciones | igual, con ruido |
| `section` inglés | 564 / 17 691 | 3 | convergencia intra-artículo **0.0**; una fusión **falsa** `it@Q153238#1 ~ it@Q9123#5` con `ϕ = 0.9626` |
| `pairs` | 178 / 4 120 | ver §9.3 | el único régimen con señal |

El resultado de `section` enseña algo: las secciones de un mismo artículo **no repiten hechos**. El
encabezado dice que ganó el Nobel y la sección de carrera dice que fue nombrado profesor. Sus
configuraciones son disjuntas en 4 de los 5 casos inspeccionados. Dividir un texto no fabrica
fuentes independientes. La fusión falsa entre dos `it` fue el motivo de introducir la guarda de dos
configuraciones informativas compartidas.

### 9.3 Corpus real: régimen `pairs` por descompositor

| Métrica | heurístico | LLM | ambos |
|---|---|---|---|
| declaraciones | 2 931 | 11 242 | 13 574 |
| símbolos / variables | 4 120 / 690 | 10 703 / 4 427 | 12 277 / 5 701 |
| pares candidatos | 37 | 275 | 326 |
| declaraciones por símbolo (media / mediana) | 1.42 / 1 | 2.10 / 1 | 2.21 / 1 |
| configuraciones compartidas por par correcto (media) | 0.49 | 1.28 | 1.53 |
| **convergencia entre fuentes** | **1/77 = 0.013** | **5/79 = 0.063** | **8/81 = 0.099** |
| pronombre↔pronombre / etiqueta↔etiqueta / pronombre↔etiqueta | 0/78, 1/38, 0/105 | 2/76, 1/47, 2/116 | 6/80, 1/49, 2/122 |
| intra-contexto | 0/157 | 0/158 | 0/161 |
| **MRR / acierto en 1 / acierto en 3** | 0.055 / 0.043 / 0.053 | **0.265 / 0.250 / 0.261** | 0.243 / 0.219 / 0.250 |
| consultas con candidato | 13 de 94 | 34 de 92 | 38 de 96 |
| **falsas fusiones** | **0** | **0** | 1 |
| preguntas Wikidata: cobertura etiqueta / con salto | 0.002 / 0.0 | 0.011 / 0.048 | 0.012 / 0.045 |
| precisión de las respuestas | 1.0 | 1.0 | 1.0 |
| basura aislada: plantada frente a real | 1.0 / 0.98 | 1.0 / 0.96 | 1.0 / 0.92 |
| promovidos / propuestos / referentes | 6 / 65 / 3 | 45 / 296 / 18 | 98 / 352 / 42 |
| memoria / tiempo | 198 MB / 2.5 s | 250 MB / 10.2 s | 274 MB / 14.4 s |

Pares convergidos con el descompositor LLM, todos correctos:

| Par | Tipo | `ϕ` | Configuraciones compartidas |
|---|---|---|---|
| `bose@Q45789 ~ he@Q45789#0` | pronombre↔etiqueta, equivalente | 0.9976 / 0.9913 | 9 |
| `charles_francis_richter@Q184014#0 ~ …@Q184014` | etiqueta↔etiqueta | 0.9921 | 7 |
| `he@Q215022 ~ he@Q215022#0` (Eddington) | pronombre↔pronombre | 0.9868 | 5 |
| `atmosphere@Q179777 ~ atmosphere@Q179777#0` | término↔término | 0.9864 / 0.9780 | 5 |
| `he@Q1219622 ~ chizhevsky@Q1219622#0` | pronombre↔etiqueta | 0.9805 | 4 |
| `arthur_holmes@Q606039 ~ …#0` | etiqueta↔etiqueta | 0.9813 | 4 |
| `urey@Q179777 ~ urey@Q179777#0` | etiqueta↔etiqueta | 0.9606 | 3 |

El caso de Bose merece atención y se traza completo en el Apéndice D. El artículo Simple habla de
`bose` y el encabezado en inglés, de `he`. Ninguna cadena coincide. Nueve configuraciones
compartidas, las nueve disciplinas que ambas fuentes le atribuyen, bastan para que el sistema
concluya que son el mismo referente **en ambos sentidos**, sin haber resuelto nunca el pronombre.

### 9.4 Anatomía de los fallos

Diez personas inspeccionadas con el descompositor heurístico:

| Persona | Simple | Encabezado en inglés | Configuraciones | Compartidas |
|---|---|---|---|---|
| Q102291 | `aston` | `he` | 4 / 1 | 1 (`instance\|a\|fellow`) |
| Q102830 | `he` | `he` | 3 / 2 | 1 (`award\|a\|nobel prize`) |
| Q12658 | `he` | `he` | 3 / 3 | 0 |
| Q127234 | `he` | `he` | 4 / 4 | 1 (`has_property\|a\|first`) |
| Q131729 | `bragg` | `bragg` | 1 / 5 | 0 |
| Q133544 | `baird` | `baird` | 13 / 2 | 0 |

Hay dos causas, y ninguna es la regla de promoción:

1. **Soporte.** Los símbolos tienen entre 1 y 4 configuraciones. Por la ley de §5.8, con 1 o 2 no
   pueden superar 0.87 aunque coincidan en todo.
2. **Lexicalización de los objetos.** Las dos fuentes cuentan los mismos hechos con objetos
   distintos: `Nobel Prize` frente a `Nobel Prize in Chemistry` frente a `1921`; `Cambridge` frente a
   `University of Cambridge`. Como los objetos todavía no han convergido, las configuraciones que
   deberían ser la misma tienen claves distintas. Es un problema de arranque: los sujetos no
   convergen porque los objetos no han convergido, y los objetos tienen todavía menos soporte.

---

## 10. Discusión

**Lo que los resultados sostienen.** Primero, el principio de aislamiento: los hechos plantados
quedan fuera en el 100 % de los casos, en todos los regímenes y con todos los descompositores, sin
ningún componente dedicado a detectar ruido. Segundo, la direccionalidad: las proyecciones
promovidas van del símbolo pobre al rico. Tercero, la seguridad: cero fusiones falsas en los dos
modos principales y precisión 1.0 en las respuestas. El sistema prefiere callar. Cuarto, la tesis
del LLM como descompositor de superficie: sin darle ninguna autoridad lógica, multiplica por cinco la
convergencia entre fuentes, casi por cinco el rango recíproco medio, y lleva la cobertura de las
preguntas con salto de 0.0 a 0.048.

**Lo que los resultados no sostienen todavía.** Una convergencia de 5 de 79 no es un sistema de
correferencia utilizable. La convergencia intra-contexto es 0 en los tres modos: dentro de un mismo
artículo, el pronombre y el nombre propio comparten como mucho una configuración informativa, porque
cada oración usa uno u otro y cuenta un hecho distinto. Es el resultado más incómodo y el más
instructivo: la correferencia clásica **no se recupera** por convergencia dentro de un solo texto
corto. Hace falta que otro texto diga lo mismo.

**El coste de la cobertura.** Combinar ambos descompositores sube la convergencia a 8 de 81, pero
introduce una fusión falsa y baja el rango recíproco medio. Más declaraciones ruidosas crean más
candidatos espurios. El modo LLM solo es el mejor equilibrio medido.

**La tesis del volumen.** «La calidad sube con la cantidad» queda confirmada en su forma débil, ya
que más declaraciones por símbolo producen más convergencia de manera monótona entre los tres modos,
y cuantificada por la ley de soporte mínimo. Su forma fuerte, con muchas fuentes por entidad, **no se
ha probado**: el corpus tiene dos contextos por persona. Es la predicción más clara que deja este
trabajo: con `k` fuentes independientes por entidad, las configuraciones corroboradas crecen y el
umbral de tres se alcanza.

---

## 11. Amenazas a la validez

- **Tamaño y dominio.** 89 personas de un solo dominio biográfico, en inglés. Las biografías tienen
  relaciones muy estereotipadas, lo que favorece al descompositor heurístico.
- **Verdad de referencia por identidad de artículo.** Mide la convergencia de los símbolos sujeto y
  no dice nada sobre la corrección de las convergencias entre objetos (`atmosphere`, `astronomy`),
  que se inspeccionaron a mano.
- **El sintético es favorable por construcción.** Repite su núcleo de hechos en cada artículo y por
  eso desactiva el filtro de tautología. Demuestra que el algoritmo funciona con soporte, no que el
  soporte exista en texto real.
- **Dependencia del descompositor.** Las métricas de extremo a extremo mezclan extracción y
  convergencia. Se reportan declaraciones por símbolo y configuraciones compartidas por par correcto
  para poder separarlas.
- **Configuraciones no independientes.** El soporte cuenta configuraciones, no hechos independientes.
  Una enumeración en una sola oración puede aportar casi todo el soporte de un par, como en el caso
  trazado en el Apéndice D, y el modelo de Poisson las trata como evidencias separadas.
- **Un solo modelo de lenguaje y una sola corrida** de descomposición, que queda cacheada.
- **GAP no evalúa nada aquí**: su cobertura es 0.
- **Umbrales fijos** (`0.90`, `0.95`, `0.30`, soporte 2) elegidos antes de medir y no ajustados
  después. No se hizo un barrido de sensibilidad.
- **El cambio de semántica del ranking** tras el rediseño: las cifras anteriores (0.104 y 0.287) se
  calculaban sobre la fila completa y no son comparables con las actuales.

---

## 12. Trabajo futuro

1. **Canonicalización de objetos por convergencia**, aplicando `equivalent` a los objetos antes que
   a los sujetos y aprovechando inclusiones léxicas como evidencia (`nobel prize` dentro de `nobel
   prize in chemistry`), para romper el problema de arranque de §9.4.
2. **Más fuentes por entidad**: otras ediciones de Wikipedia, enciclopedias y obituarios, para
   probar la forma fuerte de la tesis del volumen.
3. **Una medida adaptada a soporte pequeño.** La ley de §5.8 sugiere estudiar umbrales que dependan
   del soporte, o combinar la intensidad con el número de contextos que corroboran.
4. **Convergencia estrictamente incremental**, puntuando solo los pares que tocan al lote nuevo.
5. **Taxonomía a escala**: la construcción de la jerarquía es cuadrática por nivel en Python y hoy se
   limita a las 600 características más frecuentes.
6. **Curado asistido**: medir cuántos de los 296 candidatos propuestos confirma un humano y cuánto
   mejora la cobertura de las preguntas.
7. **Causalidad y aceleración por hardware**, fuera del alcance actual.

---

## 13. Reproducibilidad

Entorno: Python 3.13.5, NumPy 2.1.3, SciPy 1.15.3, sin GPU, 15 GB de memoria. Toda corrida pesada va
bajo tope de memoria y de a una por comando.

```bash
# tests: 131 en la raíz y 179 en el motor
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/
( cd matrix && PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider )

# corpus: requiere red una sola vez; los textos y la caché LLM están versionados
python -m corpus.physicists.build
python -m pipeline.decompose_batch corpus/physicists --regime pairs --backend pi

# evaluación, una corrida por comando
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer heuristic --out /tmp/eval/pairs_heuristic
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer llm       --out /tmp/eval/pairs_llm
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer both      --out /tmp/eval/pairs_both

# conversación
cd matrix && PYTHONPATH=.. python -m prototypes.shrdlu.repl ../corpus/physicists/en --lang en
```

Cada corrida escribe `metrics.json` y `report.md` con los pares convergidos, diez fallos con sus
configuraciones, las configuraciones tautológicas descartadas y las fusiones falsas.

---

## Apéndice A. Notación

| Símbolo | Significado |
|---|---|
| `signo@ctx` | símbolo: signo normalizado en su contexto de declaración |
| `(R a b)@ctx` | declaración de la relación `R` entre dos símbolos de `ctx` |
| `R\|rol\|ref(x)` | configuración: papel en `R` frente al co-participante `x` |
| `WiGame(ctx, R)` | juego de lenguaje de la relación `R` en el contexto `ctx` |
| `S_i`, `V_i` | forma lógica y valores de verdad del juego `i` |
| `n, n_s, n_t, n_st, n_{s∧¬t}` | contingencia del par `(s,t)` sobre las configuraciones |
| `λ`, `q`, `ϕ`, `τ`, `φ` | esperanza de contraejemplos, índice, intensidad clásica, inclusión, intensidad entrópica |
| `ref:k` | referente convergido |

## Apéndice B. Parámetros

| Parámetro | Valor | Papel |
|---|---|---|
| `min_support` | 2 | declaraciones mínimas para ser variable y configuraciones mínimas compartidas para ser candidato |
| `min_contexts` | 2 | contextos que deben corroborar una configuración |
| `taut_df` | 0.30 | frecuencia documental a partir de la cual una configuración es tautológica |
| `phi_min` | 0.90 | umbral para proponer |
| `PROMOTE_PHI` | 0.95 | umbral para promover sin curado |
| configuraciones informativas compartidas | ≥ 2 | guarda contra coincidencias estructurales |
| `max_config_size` | 500 | tamaño máximo de una configuración que genera pares |
| `max_iter` | 5 | pasadas del punto fijo |
| `batch_size` | 40 | contextos por lote |
| medida | intensidad clásica | Poisson exacta si `λ ≤ 4` |

## Apéndice C. Cronología de decisiones

| Commit | Decisión |
|---|---|
| `d505311` a `3b988fe` | repositorio inicial, paquete `sia` desde el libro, specs como delta sobre Matrix |
| `1e447a0` a `d4cc05c` | primer puente por co-ocurrencia, que resultó conceptualmente erróneo (§4) |
| `fff87d5` | `convergence.md`: símbolo igual a signo más contexto; CHIC solo mide convergencia |
| `ecabc8e`, `b4c6f2f` | contextos con signos locales; descomposición e ingesta por contexto |
| `83a866f` | taxonomía, convergencia de símbolos y mantenimiento de juegos; sintético en verde |
| `97969f4` | corpus de físicos |
| `2f8a41a` | consultas ruteadas y evaluación |
| `cc12bb0` | régimen de secciones: convergencia 0 y una fusión falsa |
| `d30570a` | régimen `pairs`, filtro de tautología, guarda de dos configuraciones |
| `28cd050` | rediseño aglomerativo: pares candidatos, lotes y tope de memoria |
| `8ebd7c2` | descompositor LLM cacheado y ranking sobre todas las consultas |
| `da21ea3` | retiro del puente viejo; código, specs y documentación alineados |

## Apéndice D. Una convergencia trazada

Satyendra Nath **Bose** (`Q45789`). El artículo de Simple English habla de `bose@Q45789` y el
encabezado de la Wikipedia en inglés habla de `he@Q45789#0`. El descompositor LLM emite 48
declaraciones en el primer contexto y 52 en el segundo. El símbolo `bose` entra en 11
configuraciones y el símbolo `he` en 19. Las que comparten son nueve, y son estas:

```
field|a|physics      field|a|mathematics   field|a|chemistry
field|a|biology      field|a|mineralogy    field|a|philosophy
field|a|arts         field|a|literature    field|a|music
```

Las dos fuentes, escritas por personas distintas, coinciden en describir a Bose como un polímata y
enumeran las mismas disciplinas. Ninguna de esas configuraciones es tautológica (ninguna aparece en
más del 30 % de los contextos) y todas están corroboradas por dos contextos. Con nueve
configuraciones compartidas, `ϕ(bose, he) = 0.9976` y `ϕ(he, bose) = 0.9913`: la primera es casi el
máximo teórico de la tabla de §5.8 y la segunda es algo menor porque `he` tiene diez configuraciones
que `bose` no ocupa. Ambas superan 0.95, así que el par se promueve a `equivalent` y recibe el
referente `ref:12`. Desde ese momento una pregunta sobre `bose@Q45789` alcanza los hechos que solo
el artículo en inglés declara sobre `he`, con la cita de ese artículo y la ruta seguida. En ningún
punto se resolvió el pronombre: se midió que sus usos coinciden.

El caso también muestra un límite. Las nueve configuraciones salen de **una enumeración**: una sola
oración de cada fuente aporta casi todo el soporte. El algoritmo cuenta configuraciones, no hechos
independientes, y una lista larga pesa como nueve evidencias. Aquí la conclusión es correcta, pero la
medida sobrestima la independencia de la evidencia (§11).

## Apéndice E. Glosario

- **Aglomerativo.** Que crece por incorporación de contextos al mundo existente, en lugar de
  recalcular todo contra todo.
- **Compuerta (`C_k`).** Coordenada verdadera para todo un subconjunto del juego, que delimita un
  subjuego.
- **Configuración.** Papel de un símbolo en una relación frente a un co-participante.
- **Discriminante (`D_i`).** Coordenada que separa dos sujetos que colisionan.
- **Proyección.** Identidad direccional entre símbolos de contextos distintos para una relación.
- **Referente.** Clase de símbolos promovidos a equivalentes.
- ***Sinnlos* / *unsinnig*.** Vacío por tautológico, y absurdo por violar la forma lógica. Ninguno se
  deriva de frecuencias, salvo la tautología relativa al corpus de §5.2, que solo excluye una
  configuración de la medida y no afirma nada sobre el mundo.

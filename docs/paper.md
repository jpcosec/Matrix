# Indexar por contextos, proponer por convergencia, interpretar con lenguaje: la capa no cognitiva de Matrix y sus límites

**Documento técnico para publicación.** Este trabajo es la **contraparte empírica** de dos piezas
del repositorio original de Matrix (`jpcosec/Matrix`), y está escrito para leerse junto a ellas:

- el *position paper* **«Logical and Semantic Guarantees in LLMs Require More Than Continuous
  Embeddings»** (`paper_v2/`), citado aquí como **[PP]** con su sección;
- la documentación operativa del motor, en particular **«WiGame, Context and Disambiguation»**
  (`docs/context_and_wigame.md`, **[CW]**), el **pipeline de ingesta** (`docs/language_to_matrix_pipeline.md`,
  **[LP]**) y el **harness de KBs** (`docs/kb_fanout_harness.md`, **[KH]**), con sus KBs versionadas de
  Wikipedia (`examples/kb_wikipedia_*`).

[PP] cierra diciendo que establece los fundamentos «without presenting empirical evaluation
metrics». [CW] afirma que acumular contextos desambigua un símbolo, y que la identidad entre
contextos «is a reviewed decision, not an automatic normalization». [KH] materializa esa identidad
como una curación manual en `aliases.yaml`. Este documento toma esas tres afirmaciones y les pone un
mecanismo y números: **qué propone esos alias, con qué evidencia, cuándo puede hacerlo y cuándo
no**. La sección 10 recorre el trabajo original afirmación por afirmación y dice, para cada una, si
nuestros resultados la confirman, la matizan o la contradicen.

Estado del repositorio: `main` (2026-09-21). Todo número citado sale de una corrida reproducible
(§14) y de los informes por etapa en `.herdr/*_report.md`. Donde un resultado es malo, se reporta
malo: ningún umbral se ajustó para mejorar una métrica.

---

## Resumen

El *position paper* de Matrix sostiene que las garantías lógicas y semánticas exigen una capa
discreta de mundos locales con verdad `V_i` y sentido `S_i`, y deja dos cosas abiertas: no presenta
evaluación empírica, y admite que el mapeo de palabras a símbolos es probablemente estocástico y
ajeno a la lógica formal. La documentación posterior del motor precisa la arquitectura: no se busca
una base de conocimiento universal ni una descripción cerrada de las cosas. Se **indexa por
contextos**, se construye un `W_i` **de los contextos**, y al crecer esa jerarquía el árbol se va
desambiguando: lo que un símbolo denota es la hoja donde convergen sus ocurrencias. La identidad
entre contextos es una decisión revisada.

Este trabajo construye y mide la **capa no cognitiva** de esa arquitectura: la que trocea el texto
en contextos, indexa los signos donde ocurren, y usa el Análisis Estadístico Implicativo (SIA/CHIC)
para **proponer** estructura: anidamientos entre contextos, compuertas, dimensiones discriminantes y
vínculos de identidad entre ocurrencias de contextos distintos. Esa capa no interpreta. La
interpretación se hace con lenguaje, por un modelo de lenguaje o una persona que lee las oraciones
citadas y decide en una compuerta de revisión. Signo lingüístico y símbolo lógico no están en
relación uno a uno, y ningún conteo puede establecer esa relación por sí solo. La pregunta que
respondemos no es si la estadística resuelve la referencia, sino **qué puede poner delante del
intérprete, con cuánta evidencia, y cuándo no tiene nada que ofrecer**.

Evaluamos sobre un corpus sintético con referentes conocidos y sobre un corpus real de 89 físicos
(Simple English Wikipedia, Wikipedia en inglés, Wikidata y GAP). En el sintético el `W_i` de
contextos separa los dos referentes con pureza 100 %, las ocurrencias de `she` se agrupan con el
nombre propio correcto en 15 de 15 artículos y los 10 hechos falsos plantados quedan aislados. En
texto real la capa propone poco: con un descompositor heurístico el vínculo correcto entre fuentes
alcanza el umbral de propuesta fuerte en 1 de 77 personas; con un LLM pequeño como descompositor de
superficie, en 5 de 79, y el candidato correcto queda primero en el 25 % de las consultas, sin
ningún vínculo falso. Derivamos una **ley de soporte mínimo** que explica esos números: con inclusión
perfecta la intensidad depende solo del número de configuraciones de la ocurrencia, y una propuesta
fuerte exige al menos tres configuraciones corroboradas, mientras que la mediana real es una
declaración por signo.

La prueba más directa es contra el repositorio original. Sobre las 699 propuestas de su KB de diez
artículos de Wikipedia, con los 70 pares de alias que una persona escribió leyendo el texto, la capa
estadística no alcanza el umbral para ninguno y no propone ningún vínculo falso. Ningún par comparte
tres configuraciones, y los mejores candidatos miden 0.863 frente al techo de 0.865 que la ley
predice para dos. Ese resultado no es un fracaso de la arquitectura sino su confirmación: **lo que el
curador hizo leyendo no se puede hacer contando**. Lo que la capa sí aporta es un orden de candidatos
y una medida de cuándo hay evidencia y cuándo no. El experimento que falta, y que este trabajo deja
planteado, es el del circuito completo: el intérprete lingüístico decidiendo sobre las propuestas.

Documentamos además un fallo de ingeniería con valor general. La primera implementación comparaba
todas las ocurrencias contra todas en matrices densas: 7.9 GB con 4 427 variables y muerte por falta
de memoria con 5 701. El rediseño **aglomerativo**, que calcula la intensidad solo sobre pares
candidatos obtenidos de un índice invertido e ingiere los contextos por lotes, baja el pico a 250 MB
y el tiempo de 245 s a 10 s. La versión cuadrática no era solo cara: contradecía el modelo.

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

Matrix propone otra cosa. [PP] argumenta que la falta de fiabilidad de los modelos de lenguaje es
representacional antes que informacional, porque un espacio continuo confunde la falsedad con la
inaplicabilidad. Su tesis, tomada del *Tractatus*, es que el significado de un signo es su
uso dentro de un juego de lenguaje, y que lo que tiene sentido o no lo tiene está fijado por la
forma lógica del juego, no por la frecuencia con que algo se dijo. De ahí se sigue una consecuencia
de diseño que organiza todo este trabajo, y que [CW] ya enuncia cuando dice que lo que un símbolo
denota es «the path/leaf where its occurrences converge»: **no hay que desambiguar antes de poblar;
la desambiguación es lo que ocurre cuando la jerarquía de contextos crece**. Y una segunda, igual de
importante: si el significado es uso dentro de un juego, establecerlo es un acto de interpretación
lingüística, y ningún procedimiento que solo cuente puede ejecutarlo.

### 1.2 La tesis

> Matrix no busca una base de conocimiento universal ni una descripción cerrada de las cosas. Indexa
> según contextos, construye un `W_i` de los contextos, y al crecer esa jerarquía el árbol se
> desambigua. Signo lingüístico y símbolo lógico no están en relación uno a uno: el símbolo es una
> posición en el espacio lógico, y el signo es solo la interfaz. Por eso **ningún algoritmo no
> cognitivo puede, por sí solo, hacer que el sistema funcione**. El troceo y la estadística pueden
> *proponer*: qué contextos anidan en cuáles, qué ocurrencias de contextos distintos se usan igual,
> qué columna es una compuerta, qué dimensión separa una colisión. La *interpretación* se hace con
> lenguaje, por un modelo o una persona que lee las oraciones citadas y decide. Un hecho espurio no
> encuentra configuraciones compatibles en otros contextos y llega al intérprete sin respaldo.

### 1.3 Contribuciones

1. **Una capa de indexación por contextos** con ocurrencias `signo@contexto`, sin catálogo global,
   con procedencia exacta por hecho (documento, desplazamiento, extractor, nivel epistémico), y una
   separación explícita entre esa dirección de ocurrencia y el símbolo lógico (§3.2).
2. **Una capa de propuesta estadística** que usa la intensidad de implicación de SIA en tres
   matrices: contextos × declaraciones para el `W_i` de contextos, configuraciones × ocurrencias
   para los vínculos de identidad, y sujetos × coordenadas para el mantenimiento de cada juego. En
   ninguna produce hechos, sentido, relaciones ni identidad: ordena candidatos para el intérprete.
3. **Una caracterización de lo que esa capa puede y no puede proponer**: la ley de soporte mínimo,
   que liga el umbral con el número de configuraciones por ocurrencia y predice los valores medidos,
   y dos filtros (corroboración y tautología) con sus condiciones de validez.
4. **Una evaluación contra la curación manual del repositorio original**, que mide la distancia entre
   lo que se puede contar y lo que hay que leer.
5. **Un rediseño aglomerativo** con memoria acotada por el número de declaraciones, junto con el
   registro del fallo que lo motivó y una barrera operativa contra procesos desbocados.
6. **Un diálogo explícito con el trabajo original** (§10): diecisiete afirmaciones de [PP], [CW],
   [LP] y [KH] contrastadas con nuestros resultados.
7. **Un protocolo de evaluación** con cuatro regímenes, tres descompositores, verdad de referencia
   externa (Wikidata, identidad de artículo) y métricas que separan la señal de la capa estadística de
   la calidad de la extracción.

---

## 2. Antecedentes

### 2.1 El trabajo original: qué afirma y qué deja abierto

[PP] sostiene que los *embeddings* continuos no bastan como sustrato semántico y que hace falta una
capa discreta, de alcance local, donde el signo lingüístico quede separado de la estructura lógica.
Su tesis central es que la alucinación es también un problema de **representabilidad**: un sistema
debería rechazar lo que no puede expresarse en la gramática local del sentido. De ese trabajo
tomamos, sin modificarlas, las piezas siguientes.

- **La partición del mundo `W_i`** ([PP] §3): un contexto, un espacio lógico `L_i` de coordenadas
  admisibles, una matriz booleana de verdad `V_i` y una de sentido `S_i`, con la proyección operativa
  `W_i* = V_i ⊙ S_i`. En el motor, cada partición es un juego de lenguaje `WiGame`, y [CW] precisa
  que un juego es **(ejes + relación) bajo un contexto**: «Two WiGames with equal axes and relation
  but different contexts are not the same object».
- **Los tres estados de sentido** ([PP] §2): `sinnvoll`, `sinnlos` (tautología o contradicción, que
  no dice nada del mundo) y `unsinnig` (absurdo, sin coordenada en `L_i`). `S_i` es *a priori*
  respecto de los hechos: según el apéndice de representaciones cerradas de [PP], dentro de un
  contexto cerrado el sentido es casi trivial, y `S_i = 0` emerge estructuralmente **en los cruces de
  contexto**, derivable de los esquemas y no listado a mano. [CW] añade que `unsinnig` significa
  «outside this context», no falso. Nunca se estima por frecuencias.
- **Signo, símbolo y nombre** ([PP] §2): «A symbol is a sign and a structure within a logical space,
  used within a context», y un nombre es el mapeo entre signo y símbolo, «sufficiently determined by
  the context to distinguish it from other symbols». El mismo signo (`gift`) puede ser símbolos
  distintos.
- **La desambiguación algebraica** ([PP] §3): las colisiones se detectan con `(W_i ⊗ W_iᵀ) − I` y se
  resuelven inyectando una dimensión discriminante `D_i` (`rough`/`smooth` para lechuga y espinaca)
  o abriendo un subcontexto. El apéndice de auto-optimización lo convierte en mantenimiento: la
  energía `E(R) = ¼(c + i + o + d)` promueve columnas tautológicas a compuertas `C_k`, parte contextos
  y separa colisiones.
- **El camino de ingesta en cuatro etapas** ([PP] apéndice): descomposición a forma estándar,
  reducción a proposiciones candidatas `(R a b)` sin estatus de verdad, chequeo de sentido en dos
  pasos (indexación por contexto y contradicción), y cómputo matricial. [LP] lo despliega en cinco
  etapas bajo el marco superficie, significado, grafo.
- **El LLM pequeño como descompositor de superficie** que «make[s] no logical decisions».

En el motor, la deducción es álgebra booleana: una matriz de implicación `I` cuya clausura se
obtiene por elevación al cuadrado repetida, y proyecciones de enrutamiento que transportan una
consulta de un juego a otro. La verdad es trivaluada (`TRUE`, `FALSE`, `UNKNOWN`), y `UNKNOWN` es lo
que responde el sistema cuando nadie ha afirmado algo. Cada hecho lleva su procedencia
`Prov(f) = (documento, desplazamiento, confianza, extractor)`, un nivel epistémico
(`observed > confirmed > inferred > statistical`) y su estado de curado. El motor se incorporó a
este repositorio como *subtree* y se extendió con los verbos necesarios (§6.2).

Y tomamos también sus **preguntas abiertas**, que son las que este documento intenta responder:

1. [PP] reconoce en su discusión que «there is a real possibility that the mapping of words to
   symbols is unequivocally stochastic in nature», y que ese mapeo «does not belong to the realm of
   formal logic». No dice cómo tratar esa parte estocástica sin contaminar la parte lógica.
2. [PP] y [LP] ubican la resolución de signo a símbolo en la entrada, a cargo de un componente
   lingüístico: el descompositor absorbe la variabilidad del signo «including sign-to-symbol
   resolution and alias folding», y la etapa 1 de [LP] pliega sinónimos con la meta-relación
   `equivalent`. [CW], escrito después, añade dos condiciones: esa resolución es **por contexto** y
   es **una decisión revisada**, porque «surface identity» no implica identidad referencial. Las dos
   cosas son compatibles (§10.2): quien resuelve es siempre alguien que lee, nunca un conteo.
3. [CW] afirma que «with N contexts about the same domain, each additional fact splits the candidate
   set» y que el referente es «the intersection that survives every context's constraints», pero no
   da un procedimiento que lo calcule sin conocer de antemano el referente.
4. [PP] concluye sin métricas empíricas.

### 2.2 El harness de KBs: la identidad como curación manual

[KH] documenta la cadena que puebla KBs de Matrix desde texto real: agentes baratos leen un chunk y
escriben candidatos, `ingest` valida y emite propuestas `pending` con alcance de contexto, una
**compuerta de revisión** aprueba o rechaza, y `compile` materializa solo lo aprobado como
`wigame:<contexto>:<relación>`. Tres decisiones de ese diseño son el punto de partida exacto de
nuestro trabajo:

- «el mismo `(R a b)` en dos artículos son dos hechos, no uno», y [CW] explica por qué: «Collapsing
  them into one global cell destroys exactly the structure that disambiguates».
- La identidad entre contextos es **curación revisada**, guardada en `aliases.yaml` como ternas
  `(contexto, símbolo) → referente` y materializada como `RoutingProjection`. En la KB de diez
  artículos esa curación la escribió una persona: `albert_einstein/he → albert_einstein`,
  `niels_bohr/einstein → albert_einstein`, `otto_hahn/meitner → lise_meitner`. En la de Marie Curie,
  `she`, `curie` y `maria` apuntan a `marie_curie`.
- El stress del harness mide una **curva de desambiguación** por acumulación de contextos: con
  referentes sintéticos, 52 % con un contexto, 91 % con dos y 100 % con cuatro; con 172 personas de
  DBpedia, 83 % con uno y 100 % con dos. Hasta donde leemos [KH], en ese stress la identidad del
  referente viene dada (por el generador o por el identificador de DBpedia), de modo que la curva
  mide cuánto discrimina la acumulación **una vez que se sabe qué símbolos comparten referente**.

[KH] declara además su cuello de botella: «la generación O(contextos²) de pares de proyección»,
truncada por defecto a 2 000 pares. Y registra un hallazgo que reaparece en nuestro trabajo: los
homónimos existen también en código (`post_init` definido en cuatro contextos, `self` y `cls` como
falsos amigos).

Lo que falta en ese cuadro es precisamente **quién propone las filas de `aliases.yaml`**. Esa es la
pieza que aquí se construye y se mide, incluida una evaluación directa contra esa curación manual
(§9.5).

### 2.3 SHRDLU: el modelo de interacción

De SHRDLU (Winograd, 1971) no tomamos el mundo de bloques ni el planificador con retroceso, sino el
**bucle de conversación**: afirmar, preguntar, pedir una justificación (`why`), recibir una pregunta
de aclaración cuando la frase es ambigua, y definir conceptos nuevos hablando. El planificador de
Micro-Planner se sustituye por el punto fijo booleano del núcleo. El modelo de lenguaje, cuando
interviene, analiza y verbaliza; no decide la verdad de nada.

### 2.4 SIA/CHIC: la intensidad de implicación

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

### 2.5 Korel: la capa de signos

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

### 3.2 Ocurrencias, símbolos y un mapeo que no es uno a uno

El átomo `Signo_vs_Simbolo` del trabajo original fija la distinción: el signo es el medio
perceptible, y el símbolo es «la función significativa dentro de un sistema lógico: la posición en
el espacio lógico». El sistema opera sobre símbolos; el signo es solo la interfaz de entrada y
salida, y una capa de traducción en la periferia asigna signos a coordenadas de `L_i`. Esa relación
**no es uno a uno** en ninguna dirección. Un símbolo tiene muchos signos (`perro`, `dog`, un
pictograma; `she`, `Curie`, `Maria Skłodowska`). Un signo tiene muchos símbolos: `gift` es regalo en
inglés y veneno en alemán, `Curie` es Marie en una oración y Pierre en la siguiente **dentro del
mismo artículo**, y `she` cambia de referente cuando el texto cambia de sujeto.

Lo que nuestra capa construye, entonces, no son símbolos:

> **Definición 1 (ocurrencia indexada).** Una ocurrencia indexada es el par `(norm(signo), ctx)`,
> escrito `signo@ctx`. Es una **dirección**: dice dónde se usó un signo. No es un símbolo lógico.

`she@Q7186` y `she@Q7259` son dos direcciones distintas, y `curie@Q7186` y `curie@Q37463` también.
Qué símbolo ocupa cada dirección es una pregunta de interpretación. La normalización se limita a
minúsculas y separadores, y sirve como evidencia superficial para la estadística y nada más. En el
código estas direcciones se llaman `Symbol` por herencia del motor; en este documento las llamamos
ocurrencias o signos contextuales para no confundir los dos planos.

Dos consecuencias, una de diseño y una limitación declarada:

- **Diseño.** La pregunta «¿qué significa este signo?» no se responde con el string ni con una
  tabla, sino, en palabras de [CW], con «the path/leaf where its occurrences converge»: la ruta del
  árbol de contextos donde esas ocurrencias caben. El refinamiento del árbol es lo que desambigua.
- **Limitación.** Nuestra implementación trata cada `signo@ctx` como **un solo nodo**. Eso impone de
  hecho un mapeo uno a uno *dentro de cada contexto*, que es falso cuando `Curie` o `she` cambian de
  referente dentro de un mismo artículo. La salida correcta, según el átomo
  `Juego_de_Desambiguacion`, es refinar: partir el contexto en subcontextos hasta que el signo sea
  unívoco en la hoja. El régimen por secciones va en esa dirección y no basta (§9.2).

### 3.3 Quién decide: la estadística propone, el lenguaje interpreta

Ningún componente de esta capa es cognitivo. El troceo cuenta caracteres y encabezados; el índice
cuenta ocurrencias; CHIC cuenta contraejemplos. Ninguno lee. Por eso su salida tiene siempre el
estatus de **propuesta**, y el circuito completo de Matrix tiene tres momentos donde interviene el
lenguaje:

1. **Al descomponer**: un modelo de lenguaje (o una heurística pobre que lo imita) convierte
   oraciones en candidatas `(R a b)`. Es el primer acto de interpretación, y por eso [PP] lo confía a
   un modelo y no a una regla.
2. **Al interpretar las propuestas**: alguien que lee, modelo o persona, recibe un candidato con las
   configuraciones compartidas y las oraciones citadas, y decide si dos ocurrencias son el mismo
   símbolo, si un contexto anida en otro, si una columna es una compuerta. Es la compuerta de
   revisión de [KH].
3. **Al conversar**: el bucle tipo SHRDLU analiza la pregunta y verbaliza la respuesta.

La capa estadística sirve a los tres sin sustituir a ninguno: reduce lo que el intérprete tiene que
mirar, ordena los candidatos, y le dice cuánta evidencia hay detrás de cada uno. Esto tiene una
consecuencia metodológica que gobierna el resto del documento: **una capa que propone se evalúa como
proponente** (cobertura, orden de los candidatos, vínculos falsos ofrecidos con confianza alta), no
por cuántas decisiones acierta sola.

### 3.4 Declaraciones y configuraciones

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

### 3.5 Qué aporta cada pieza

| Pieza | Aporta | No aporta |
|---|---|---|
| Capa de signos (Korel) | contextos, signos locales, desplazamientos, índice de enrutamiento | símbolos globales, hechos, sentido |
| Descompositor (heurística o LLM) | candidatos `(R a b)` por oración con signos locales | decisiones lógicas, resolución de pronombres |
| Motor Matrix | juegos por `(contexto, R)`, sentido, verdad trivaluada, deducción, proyecciones, procedencia y curado | estadística |
| SIA/CHIC | **propuestas** ordenadas en tres matrices (§5.6), con su evidencia | hechos, sentido, relaciones, identidad, interpretación |
| Intérprete lingüístico (LLM o persona) | la decisión: qué símbolo ocupa una ocurrencia, qué contexto anida en cuál, qué propuesta se aprueba | — |

---

## 4. El primer puente, y por qué estaba mal

Conviene contar el error, porque es el error natural. La primera versión del puente entre texto y
motor (commits hasta `d4cc05c`) construía una matriz *oraciones × conceptos*, corría CHIC sobre ella
e introducía los arcos del grafo implicativo en `V_i` bajo una relación ficticia `implies`. Además
derivaba candidatos a `unsinnig` de los pares de conceptos que nunca co-ocurrían, plegaba alias a la
entrada y deduplicaba entre contextos. La métrica de éxito era «recuperación con procedencia».

Eso es, con otro nombre, un grafo de conocimiento por co-ocurrencia, que es precisamente lo que
Matrix rechaza. [PP] lo dice sin ambigüedad en su discusión: los grafos de conocimiento capturan
«semantic co-occurrence» pero no «logical paths», y no tienen categoría para las combinaciones mal
formadas. Confunde tres planos que el *Tractatus* separa: lo que **se dijo** (hechos de un
juego), lo que **puede decirse** (forma lógica), y lo que **suele decirse junto** (frecuencia). Una
regularidad estadística no es un hecho ni una regla de sentido, y que algo no se haya dicho no lo
vuelve absurdo.

La corrección, escrita en `specs/convergence.md`, reduce la estadística a un único papel: **medir
cuánto convergen los usos**. Todo lo demás del primer puente se eliminó del código (`da21ea3`).

---

## 5. La capa de propuesta

Esta sección describe lo que la capa no cognitiva calcula. Todo lo que sale de ella es una
propuesta para el intérprete (§3.3). Tiene tres salidas, una por cada matriz de la tabla de §5.6, y
su orden de importancia arquitectónica es el de esa tabla: primero el **`W_i` de contextos**, que es
el objeto que al crecer desambigua; después los **vínculos de identidad entre ocurrencias**, que son
la evidencia con que el intérprete decide alias y proyecciones; y por último el **mantenimiento de
cada juego**. Las subsecciones 5.1 a 5.5 y 5.8 detallan la segunda salida, porque es la que más
trabajo de medición exigió y la que tiene una teoría cerrada (la ley de soporte), no porque sea el
centro del modelo. La primera salida es la menos evaluada de este trabajo, y lo decimos en §12.

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
  Ser físico no identifica a ningún físico. Es el mismo movimiento que [PP] §3 hace con `vegetable` y `food`, que son
  verdaderas para todo objeto de `W_i` y se retiran «to facilitate further analysis», trasladado del
  juego al corpus.

### 5.3 Intensidad sobre pares candidatos

No se calcula la intensidad entre todos los pares de símbolos (§7). Un índice invertido
configuración → símbolos genera los **pares candidatos**: pares ordenados `(s,t)` que comparten al
menos una configuración, con `n_st` el número de configuraciones compartidas. Para cada candidato
se arma la contingencia `(n, n_s, n_t, n_st, n_{s∧¬t})` en arreglos de una dimensión y se evalúa
`ϕ(s,t)` con el mismo núcleo numérico que la versión densa (igualdad verificada con tolerancia
`1e-9`). La medida por defecto es la **clásica**: en texto real `λ` es pequeño y el índice
entrópico castiga cada contraejemplo con demasiada fuerza, mientras que la clásica es exactamente
el modelo de Poisson del libro.

### 5.4 Regla de propuesta y política de promoción

Para un candidato `(s,t)` con `ϕ(s,t) ≥ φ_min = 0.90`:

1. Si `ϕ(t,s) ≥ 0.90` también, el par se propone como **`equivalent`**: las dos ocurrencias se usan
   igual en ambos sentidos.
2. Si solo un sentido supera el umbral, se propone una **`projection`** direccional `s → t`, por cada
   relación que ambos comparten, y solo entre contextos distintos.
3. Cada propuesta viaja con su evidencia: las configuraciones compartidas, los contextos que las
   corroboran y las oraciones citadas. Es lo que el intérprete lee para decidir.

Una propuesta es **fuerte** cuando la intensidad supera 0.95 (en ambos sentidos para `equivalent`),
las ocurrencias comparten al menos 2 configuraciones informativas y esas configuraciones provienen
de al menos 2 contextos. Si las dos ocurrencias viven en el mismo contexto, basta con las 2
configuraciones compartidas.

**Sobre la promoción automática.** La implementación actual promueve las propuestas fuertes sin
pasar por el intérprete, y guarda los grupos resultantes como referentes (`system.referents`,
`system.equivalences`) con su evidencia y su estado de curado, de modo que son reversibles. Esa
promoción es un **atajo experimental**: permitió medir la capa aislada, sin el coste ni la varianza
de un intérprete en el circuito. No es el punto de decisión de la arquitectura. En los términos de
[KH] es un revisor determinista, del mismo tipo que `--reviewer ast` en el corpus de software, y
como política debe poder apagarse: en el circuito completo todas las propuestas, fuertes o no, van
a la compuerta de revisión, y la intensidad solo ordena la cola. Cuando este documento dice que un
par «converge» o «se promueve», debe leerse como «la capa lo propone con evidencia fuerte».

Los candidatos se procesan en orden `(−ϕ, s, t)` para que el resultado sea determinista.

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

El tercer uso es la versión estadísticamente asistida del mantenimiento por energía `E(R)` del
apéndice de [PP]: promoción de columnas tautológicas a compuertas, división en subcontextos y
separación de colisiones de `W_i ⊗ W_iᵀ − I`. CHIC no decide ninguna de esas mutaciones; ordena los
candidatos. En el corpus de vegetales, que es el ejemplo de referencia de [PP] §3, el mantenimiento
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
pasar de 0.87 por muy idénticos que sean los usos**. Como `n_{¬t}/n` es algo menor que 1, en la
práctica promover a 0.95 exige cuatro. El corpus sintético necesitó unas 8
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

El flujo es el camino de ingesta de cuatro etapas del apéndice de [PP], con una diferencia y un
añadido. La etapa 1 (descomposición) y la etapa 2 (candidatas `(R a b)` sin estatus de verdad) son
las mismas, salvo que no pliegan alias. La etapa 3a (indexación por contexto) es trivial por
construcción, porque cada candidata se enruta al juego de su propio contexto de declaración, y la 3b
(contradicción) la ejerce el runtime. La etapa 4 es el cómputo matricial. El añadido es el bloque de
convergencia, que [PP] no tiene y que responde a la pregunta que [KH] resuelve a mano: qué
proyecciones existen entre los juegos.

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

El trabajo original ya contenía la advertencia. [PP] describe el conocimiento global como un
hipertensor canónico `N × |R| × N` pero añade que «operationally it materializes as a graph of dense
2D sub-matrices extracted by tensorial projection». Y [KH] midió el mismo muro desde el otro lado:
su cuello de botella es «la generación O(contextos²) de pares de proyección», que trunca a 2 000
pares. Nuestro fallo es la versión a nivel de símbolos de ese mismo cuadrático, y la salida (§7.3)
sirve para ambos.

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

Cuando hay soporte, la capa propone lo correcto: mantiene separadas las ocurrencias homónimas
(`she` en artículos de personas distintas), agrupa el pronombre con el nombre propio de su contexto,
y deja sin respaldo los hechos plantados. El sintético es favorable por construcción: cada hecho se
repite en muchos artículos, que es justo lo que falta en texto real. Y aun aquí lo que se obtiene es
una propuesta bien fundada; que `she` *sea* Marie Curie lo sabe quien lee el artículo.

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
proponga con evidencia fuerte, **en ambos sentidos**, que las dos ocurrencias se usan igual. Que
sean el mismo símbolo lo confirma quien lee las dos oraciones.

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

### 9.5 Lo que se puede contar frente a lo que hay que leer: la curación manual del repositorio original

Es el experimento que más directamente conversa con [KH]. Tomamos las propuestas con alcance de
contexto de `kb_wikipedia_10_articles` (699 declaraciones sobre Einstein, Bohr, Hahn, Meitner, los
tres Curie, Franklin, Watson y Crick, extraídas por los agentes del harness) y usamos como verdad de
referencia el `aliases.yaml` que una persona escribió a mano: 70 pares de símbolos correferentes, 33
dentro de un mismo contexto y 37 entre contextos. La capa de propuesta corre sobre esas declaraciones sin
ver los alias. Ningún umbral de intensidad se tocó; sí se variaron los dos filtros, porque el propio
experimento mostró que interactúan mal con KBs pequeñas.

| Métrica | A: filtros por defecto | B: sin corroboración | C: sin corroboración ni tautología |
|---|---|---|---|
| símbolos / variables | 1 071 / 138 | igual | igual |
| declaraciones por símbolo (media / mediana) | 1.31 / 1 | igual | igual |
| configuraciones: crudas → tras filtros | 1 118 → **20** | 1 118 → 404 | 1 118 → 407 |
| pares candidatos | 70 | 94 | 178 |
| candidatos con `ϕ ≥ 0.90` | **0** | **0** | **0** |
| promovidos / propuestos | 0 / 0 | 0 / 0 | 0 / 0 |
| **recall sobre los 70 pares de oro** | **0** | **0** | **0** |
| **fusiones falsas** | **0** | **0** | **0** |
| MRR / acierto en 1 / acierto en 3 | 0.089 / 0.049 / 0.146 | 0.146 / 0.122 / 0.195 | 0.158 / 0.122 / 0.171 |
| consultas con candidato (de 41) | 6 | 8 | 11 |
| `ϕ` máxima de un par de oro | 0.573 | 0.783 | 0.781 |
| `ϕ` máxima de cualquier candidato | 0.817 | 0.863 | 0.863 |

**Cómo leer este resultado.** El curador de [KH] escribió esos 70 alias **leyendo**: vio `she` en una
oración del artículo de Meitner y supo quién era. La capa estadística no lee; necesita que tres
hechos corroborados digan lo mismo de dos ocurrencias. Que no alcance el umbral para ninguno de los
70 pares no es un fracaso de la arquitectura de Matrix sino su confirmación empírica: **la relación
entre signo y símbolo no se establece contando**, y por eso el trabajo original pone una compuerta
de revisión donde la pone. Lo que corresponde medirle a la capa es lo que ofrece al intérprete:

- **No ofrece nada falso con confianza alta**: cero vínculos por encima del umbral, correctos o no.
- **Ofrece un orden**: el correferente correcto es el primer candidato en el 12 % de las consultas y
  está entre los tres primeros en el 20 %.
- **Cubre poco**: solo 11 de 41 ocurrencias curadas tienen algún candidato.
- **Dice por qué**: el histograma de soporte identifica, par por par, que falta evidencia y cuánta.

El histograma de configuraciones compartidas por par de oro:

| Configuraciones compartidas por el par de oro | 0 | 1 | 2 | ≥ 3 |
|---|---|---|---|---|
| sin ningún filtro | 60 | 8 | 2 | **0** |
| con los filtros por defecto | 65 | 5 | 0 | **0** |

Ningún par de oro comparte tres configuraciones, ni siquiera sin filtros, de modo que por
construcción ninguno puede pasar de 0.865. Los candidatos de mayor intensidad medidos, 0.8626 y
0.8627 con dos configuraciones compartidas, están pegados a ese techo teórico: **la ley predice el
valor con tres cifras**. De los 70 pares de oro, 44 involucran un símbolo con una sola declaración,
que ni siquiera entra en la matriz; `albert_einstein@albert_einstein` tiene exactamente una.

La señal, sin embargo, existe. En la corrida B el apellido `hahn` usado en el artículo de Meitner
tiene a `otto_hahn` **primero** entre sus candidatos, y `pierre_curie@marie_curie` tiene primero al
`pierre_curie` del artículo de Pierre. Son alias entre contextos que el curador escribió a mano y que
el ranking coloca en cabeza. En la KB de un solo artículo (`kb_wikipedia_marie_curie`), sin filtro de
tautología, `she@marie_curie` aparece primero entre los candidatos de `marie_curie@marie_curie` con
`ϕ = 0.73`: el algoritmo ve *casi* lo mismo que el curador, y con una declaración por símbolo ese
casi no alcanza.

El experimento expuso además **dos defectos de nuestro diseño** que el corpus de físicos no dejaba
ver:

1. **El filtro de corroboración impide por construcción los alias dentro de un contexto.** Con un
   contexto por artículo, las configuraciones de `she@marie_curie` y de `marie_curie@marie_curie` se
   declaran en un único contexto y se descartan antes de medir. Por eso sobreviven 20 de 1 118
   configuraciones en la corrida A, y por eso la convergencia intra-contexto fue 0 de 157 en §9.3.
   Los 33 alias intra-contexto de la curación manual son inalcanzables para la regla tal como está.
2. **El filtro de tautología degenera con pocos contextos.** El umbral es una fracción de los
   contextos. Con diez contextos descarta todo lo que aparezca en más de tres, y con uno solo lo
   descarta **todo**: la corrida sobre Marie Curie con el filtro activo tiene cero configuraciones.

---

## 10. Diálogo con el trabajo original

Esta sección recorre las afirmaciones de [PP], [CW], [LP] y [KH] que nuestro trabajo toca, y dice
para cada una qué encontramos. El veredicto usa cuatro palabras: **confirma**, **extiende**,
**matiza** y **contradice**.

### 10.1 Tabla de correspondencias

| # | Afirmación del trabajo original | Lo que hicimos y medimos | Veredicto |
|---|---|---|---|
| 1 | [PP] conclusión: el marco se presenta «without presenting empirical evaluation metrics» | protocolo con cuatro regímenes, tres descompositores y verdad de referencia externa (§8, §9); evaluación contra la curación manual de [KH], con resultado negativo (§9.5) | **extiende** |
| 2 | [CW]: «a sign such as `she` can be `sinnvoll` inside `ctx:marie_curie`»; átomo `Signo_vs_Simbolo`: el símbolo es la posición en el espacio lógico, el signo es la interfaz | definición 1: `signo@contexto` es una **dirección de ocurrencia**, no un símbolo; los pronombres se indexan y no se resuelven al indexar (§3.2) | **confirma**, con una limitación declarada: un nodo por signo y contexto |
| 3 | [CW] y [KH]: el mismo `(R a b)` en dos artículos son dos hechos; colapsarlos «destroys exactly the structure that disambiguates» | ingesta por `WiGame(ctx, R)`; la convergencia **usa** esa duplicación como evidencia: una configuración corroborada por dos contextos es la unidad de medida (§5.2) | **confirma**, y muestra para qué sirve la estructura que no se colapsa |
| 4 | [CW]: acumular contextos desambigua; el referente es «the intersection that survives», «the path/leaf where its occurrences converge» | una capa que **propone** esa intersección sin conocer el referente (§5), y una **ley de soporte mínimo** que dice cuánta acumulación hace falta para que haya algo que proponer: tres configuraciones corroboradas (§5.8) | **extiende** con una cota; el árbol de contextos, que es el mecanismo central, es lo menos evaluado aquí (§12) |
| 5 | [KH]: curva de desambiguación 52 % → 91 % → 100 % con 1, 2 y 4 contextos | con el referente **no dado** y sin intérprete, dos contextos por persona dan una propuesta fuerte para el 6 % de las personas y el candidato correcto primero en el 25 % (§9.3); sobre la KB de diez artículos de [KH], ninguna propuesta fuerte y 12 % de primeros (§9.5) | **matiza**: la curva de [KH] mide cuánto discrimina la acumulación con la identidad ya interpretada; la estadística sola llega mucho menos lejos, como el modelo anticipa |
| 6 | [CW]: la identidad entre contextos es «a reviewed decision, not an automatic normalization»; [KH] la guarda en `aliases.yaml`, escrita por alguien que leyó el texto | la capa ordena candidatos para esa decisión y adjunta la evidencia; sobre la KB real de [KH] no alcanza el umbral para ninguno de los 70 alias (§9.5) | **confirma**: lo que el curador hace leyendo no se hace contando |
| 7 | [PP] apéndice y [LP] etapa 1: el descompositor hace «sign-to-symbol resolution and alias folding» | la resolución es un acto de lectura, y [PP] acierta al confiarla a un componente lingüístico; nuestra capa no la hace ni la reemplaza, solo indexa ocurrencias y propone (§10.2) | **confirma**, con la precisión de [CW]: por contexto y revisada |
| 8 | [PP]: LLM pequeños como descompositores de superficie que «make no logical decisions» | una llamada por chunk, signos de lista cerrada, validación estricta; convergencia ×5, rango recíproco medio ×4.8, cero fusiones falsas (§9.3) | **confirma** con números |
| 9 | [PP] §3: `vegetable` y `food`, verdaderas para todo `W_i`, son *sinnlos* y se retiran antes de analizar | filtro de tautología a nivel de corpus: `instance\|a\|physicist` (54 de 178 contextos) no identifica a nadie y se excluye de la medida (§5.2) | **confirma** y traslada el principio del juego al corpus |
| 10 | [PP] §3: colisiones con `(W ⊗ Wᵀ) − I`, resueltas con un `D_i` | misma operación dentro de cada juego (§5.6), y su **generalización entre contextos**: la matriz configuraciones × símbolos detecta qué símbolos de contextos distintos «colisionan» en sus usos | **extiende** |
| 11 | [PP] apéndice `E(R)`: columnas tautológicas a compuertas, división de contextos, dimensión separadora mínima | `maintain_wigame` reproduce el ejemplo del paper (`verde` como compuerta; `hoja_lisa`/`hoja_rugosa` como `D_i` de lechuga y espinaca) y reporta `unresolved` cuando no existe separador | **confirma** sobre el ejemplo canónico |
| 12 | [PP] discusión: los grafos de conocimiento capturan «semantic co-occurrence» pero no «logical paths» | nuestro primer puente cayó exactamente en eso (§4) y hubo que retirarlo | **confirma**, por la vía dolorosa |
| 13 | [PP] discusión: el mapeo de palabras a símbolos es posiblemente «unequivocally stochastic» y no pertenece a la lógica formal | toda la estadística del sistema vive **en ese mapeo y solo ahí**; `S_i` y `V_i` no reciben nada estimado por frecuencias | **confirma** y le asigna un lugar arquitectónico |
| 14 | [PP] discusión: verificación en `O(1)` con multiplicación matricial densa; hipertensor canónico `N × \|R\| × N` | las vistas densas globales no se pueden materializar: 11 GB con 5 701 símbolos (§7). La propia [PP] dice que el hipertensor «materializes as a graph of dense 2D sub-matrices» | **matiza**: el `O(1)` vale por celda dentro de un juego, no para construir vistas globales |
| 15 | [KH]: cuello de botella en «la generación O(contextos²) de pares de proyección», truncada a 2 000 | pares candidatos por índice invertido configuración → símbolos: 326 candidatos en lugar de 32 millones (§7.3) | **extiende**: mismo problema, con una salida que [KH] puede adoptar |
| 16 | [KH]: homónimos en código (`post_init` en cuatro contextos, `self` y `cls` como falsos amigos) | predicción no probada: símbolos homónimos con configuraciones disjuntas no convergen, como `she@curie` y `she@franklin` en el sintético (§9.1) | **predice**; experimento pendiente |
| 17 | [PP] §3: hechos `UNKNOWN` (`∅`) distintos de falsos | el REPL responde «No lo sé» cuando el pronombre no converge, con precisión 1.0 en lo que sí responde (§6.4) | **confirma** |

### 10.2 Quién resuelve el signo: una lectura conjunta de [PP] y [CW]

La figura de signos y símbolos de [PP] muestra la palabra *perro*, la palabra *dog* y un pictograma
llegando «through the decomposition stage (sign→symbol resolution and alias folding) onto a single
symbol». [CW] dice que decidir que `she@marie_curie` y `curie@marie_curie` denotan el mismo referente
es «a reviewed decision, not an automatic normalization». A primera vista chocan. No chocan, y la
razón es la que organiza este documento: **en ambos textos quien resuelve es alguien que lee**. En
[PP] es el modelo de lenguaje que descompone; en [CW] y [KH] es el curador que escribe
`aliases.yaml`. Ninguno de los dos le entrega esa decisión a un conteo. Lo que [CW] añade a [PP] son
dos condiciones sobre esa lectura: que el resultado valga **por contexto** (el mismo signo puede ser
otro símbolo en otro artículo, o en otra sección del mismo), y que quede **registrado y revisable**.

Nuestra capa se ubica entonces en un lugar preciso, que no es el del intérprete. No hace resolución
de signo a símbolo y no pliega alias. Indexa ocurrencias y le propone al intérprete, con evidencia,
qué ocurrencias de contextos distintos se usan igual. El plegado de alias es un acto lingüístico que
ocurre **después** de la propuesta y **con** ella a la vista, no una etapa que la estadística pueda
ejecutar. La relación entre signo y símbolo es de muchos a muchos, y una relación así no se
reconstruye desde frecuencias: se interpreta.

### 10.3 Por qué la promoción automática es un atajo y no la arquitectura

La implementación promueve sola las propuestas fuertes (§5.4). Es justo decir por qué existe y por
qué no debe confundirse con el diseño. Existe porque hacía falta medir la capa estadística aislada:
con un intérprete en el circuito, los aciertos del conjunto no dicen nada sobre qué parte aportó
cada uno. Y es defendible como política acotada, porque [KH] ya admite revisores deterministas
(`--reviewer ast`, `--reviewer operatoria`) y porque en todas las corridas la tasa de vínculos falsos
por encima del umbral fue cero o casi cero.

Pero no es la arquitectura. En Matrix la identidad es una decisión revisada, y una intensidad de
0.98 sigue siendo un conteo: dice que dos ocurrencias comparten cuatro configuraciones corroboradas,
no que sean el mismo símbolo. El caso trazado en el Apéndice D lo muestra: las nueve configuraciones
que unen `bose` con `he` salen de una sola enumeración en cada fuente. La conclusión es correcta,
pero quien puede **saber** que es correcta es alguien que lea esas dos oraciones. La integración que
corresponde es que toda propuesta, fuerte o débil, llegue a la compuerta de revisión de [KH] como una
fila `pending` para `aliases.yaml`, con su evidencia, y que la intensidad ordene la cola.

### 10.4 Lo que este trabajo no toca del original

Para no sobrevender: no evaluamos la tesis principal de [PP] sobre los límites de los espacios
continuos (oscilación de Gibbs, teselado en politopos, el AUROC cercano al azar de los errores
dentro del canal), ni la integración de la máscara de sentido en la atención, ni la
omnirepresentación en bloques, ni la operatoria de recetas y máquinas de [KH]. Tampoco construimos
`S_i` a partir de cruces de contexto: nuestros juegos son contextos cerrados donde, como anticipa
[PP], el sentido es casi trivial. Nuestro aporte se limita al tramo que [PP] llama periferia de
signos y símbolos, y a la pregunta de cómo cruzar contextos sin destruir la estructura que los
distingue.

---

## 11. Discusión

**Lo que los resultados sostienen.** Primero, el principio de aislamiento: los hechos plantados
quedan fuera en el 100 % de los casos, en todos los regímenes y con todos los descompositores, sin
ningún componente dedicado a detectar ruido. Segundo, la direccionalidad: las proyecciones
promovidas van del símbolo pobre al rico. Tercero, la prudencia: cero vínculos falsos por encima del umbral en los dos
modos principales y precisión 1.0 en las respuestas. Una capa que propone debe, ante todo, no
ofrecer con confianza lo que es falso, y prefiere callar. Cuarto, la tesis
del LLM como descompositor de superficie: sin darle ninguna autoridad lógica, multiplica por cinco la
convergencia entre fuentes, casi por cinco el rango recíproco medio, y lleva la cobertura de las
preguntas con salto de 0.0 a 0.048.

**Lo que la capa no puede proponer.** Una propuesta fuerte para 5 de 79 personas es poca cosa, y
dentro de un mismo contexto no propone nada en ninguno de los tres modos: el pronombre y el nombre
propio comparten como mucho una configuración informativa, porque cada oración usa uno u otro y
cuenta un hecho distinto. Es el resultado más instructivo: la correferencia dentro de un texto corto
**no deja huella estadística**. Se resuelve leyendo, y la evidencia contable solo aparece cuando otro
texto dice lo mismo.

**Contar no es leer.** El experimento de §9.5 es el más honesto del trabajo, porque el oro no lo
construimos nosotros, y su lectura correcta es la tesis del documento. El curador escribió 70 alias
leyendo oraciones. La capa estadística, sobre las mismas declaraciones, no alcanza el umbral para
ninguno. Eso no mide un defecto que haya que reparar hasta que la estadística «alcance» al curador:
mide la distancia entre dos operaciones de naturaleza distinta. Interpretar un signo es un acto
lingüístico, y en Matrix lo ejecuta siempre un componente que lee. Lo que la capa no cognitiva puede
hacer por ese componente es acotarle el trabajo: decirle qué mirar primero, con qué evidencia, y
dónde no hay evidencia ninguna. Sobre esa KB hoy le ofrece el candidato correcto en primer lugar en
el 12 % de los casos. Es poco, y la ley de soporte dice exactamente por qué y cuánto habría que
crecer para que sea más.

**El objeto central es el árbol de contextos, y es lo que menos medimos.** La arquitectura
desambigua haciendo crecer la jerarquía de contextos: un `W_i` cuyos sujetos son contextos, cortado
en niveles, con compuertas y rutas, que se refina con cada contexto nuevo hasta que un signo es
unívoco en su hoja. Nuestro trabajo construye ese `W_i` y lo valida en el sintético (pureza 100 %),
pero sobre el corpus real lo dejó como opción y concentró la medición en los vínculos por pares. Es
un sesgo de este trabajo, no del modelo. Los resultados negativos de los regímenes por documento y
por sección (§9.2) apuntan al mismo sitio: partir un texto en trozos no desambigua nada si esos
trozos no se organizan en una jerarquía que el intérprete pueda recorrer.

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

## 12. Amenazas a la validez

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
- **El circuito completo no está evaluado.** Todas las cifras miden la capa estadística sola. La
  arquitectura que se defiende, con un intérprete lingüístico decidiendo sobre las propuestas, no se
  midió: no sabemos cuánto trabajo le ahorra la cola ordenada ni cuántos errores le induce.
- **El `W_i` de contextos, mecanismo central del modelo, es lo menos evaluado.** Se validó en el
  sintético y quedó como opción (`--taxonomy`, limitada a 600 características) en el corpus real.
- **Un nodo por signo y contexto.** La implementación supone que un signo denota un solo símbolo
  dentro de un contexto. Es falso para `Curie` o `she` cuando el texto cambia de sujeto, y sesga a la
  baja toda medida de vínculo para esos signos.
- **Filtros mal condicionados en KBs pequeñas** (§9.5): la corroboración entre contextos bloquea por
  construcción los alias dentro de un contexto, y el filtro de tautología, definido como fracción de
  contextos, descarta todo cuando hay un solo contexto. Ambos se midieron y ninguno se corrigió aquí.
- **Umbrales fijos** (`0.90`, `0.95`, `0.30`, soporte 2) elegidos antes de medir y no ajustados
  después. No se hizo un barrido de sensibilidad.
- **El cambio de semántica del ranking** tras el rediseño: las cifras anteriores (0.104 y 0.287) se
  calculaban sobre la fila completa y no son comparables con las actuales.

---

## 13. Trabajo futuro

00. **El experimento del circuito completo.** Entregar las propuestas ordenadas, con sus oraciones
   citadas, a un intérprete lingüístico (un LLM pequeño y, como control, una persona) que decida en
   la compuerta de revisión, y medir contra `aliases.yaml`: aciertos del intérprete con y sin la cola
   de la capa estadística, propuestas leídas por alias correcto, y errores inducidos. Es la medida
   que corresponde a la arquitectura y la que este trabajo no tiene.
01. **Hacer crecer y medir el árbol de contextos** sobre el corpus real: `W_i` de contextos por
   lotes, subcontextos donde un signo no es unívoco (estrategia B del `Juego_de_Desambiguacion`), y
   una métrica de desambiguación por profundidad de ruta comparable con la curva de [KH].
0. **Integración con el harness original.** Que la convergencia emita sus candidatos como
   propuestas `pending` para `aliases.yaml`, con las configuraciones compartidas y las oraciones
   citadas como evidencia para la compuerta de revisión de [KH]; y que `compile` genere los pares de
   proyección desde el índice invertido de referentes compartidos en lugar de recorrer
   `O(contextos²)` pares con un tope de 2 000.
1. **Canonicalización de objetos por convergencia**, aplicando `equivalent` a los objetos antes que
   a los sujetos y aprovechando inclusiones léxicas como evidencia (`nobel prize` dentro de `nobel
   prize in chemistry`), para romper el problema de arranque de §9.4.
2. **Más fuentes por entidad**: otras ediciones de Wikipedia, enciclopedias y obituarios, para
   probar la forma fuerte de la tesis del volumen.
2b. **Alias dentro de un contexto.** La corroboración entre contextos no puede proponerlos. Son el
   caso más claro de decisión que pertenece al intérprete que lee; lo que la capa puede aportar es
   evidencia local barata (posición, continuidad de sujeto entre oraciones) para ordenarle la cola, y un
   filtro de tautología con un mínimo absoluto de contextos.
3. **Una medida adaptada a soporte pequeño.** La ley de §5.8 sugiere estudiar umbrales que dependan
   del soporte, o combinar la intensidad con el número de contextos que corroboran.
4. **Convergencia estrictamente incremental**, puntuando solo los pares que tocan al lote nuevo.
5. **Taxonomía a escala**: la construcción de la jerarquía es cuadrática por nivel en Python y hoy se
   limita a las 600 características más frecuentes.
6. **Curado asistido**: medir cuántos de los 296 candidatos propuestos confirma un humano y cuánto
   mejora la cobertura de las preguntas.
7. **Causalidad y aceleración por hardware**, fuera del alcance actual.

---

## 14. Reproducibilidad

Entorno: Python 3.13.5, NumPy 2.1.3, SciPy 1.15.3, sin GPU, 15 GB de memoria. Toda corrida pesada va
bajo tope de memoria y de a una por comando.

```bash
# tests: 133 en la raíz y 179 en el motor
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/
( cd matrix && PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider )

# corpus: requiere red una sola vez; los textos y la caché LLM están versionados
python -m corpus.physicists.build
python -m pipeline.decompose_batch corpus/physicists --regime pairs --backend pi

# evaluación, una corrida por comando
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer heuristic --out /tmp/eval/pairs_heuristic
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer llm       --out /tmp/eval/pairs_llm
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer both      --out /tmp/eval/pairs_both

# contra la curación manual del repositorio original (solo lectura sobre ../Matrix)
KB=/home/jp/proyectos/Matrix/Matrix/examples/kb_wikipedia_10_articles
bash scripts/capped.sh 4 -- python -m experiments.eval_matrix_kb $KB --out /tmp/eval/mkb10_A
bash scripts/capped.sh 4 -- python -m experiments.eval_matrix_kb $KB --min-contexts 1 --out /tmp/eval/mkb10_B
bash scripts/capped.sh 4 -- python -m experiments.eval_matrix_kb $KB --min-contexts 1 --taut-df 1.0 --out /tmp/eval/mkb10_C

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

### A.1 Correspondencia con la notación del trabajo original

| Trabajo original | Aquí | Observación |
|---|---|---|
| `W_i`, partición del mundo ([PP] §3) | `WiGame(ctx, R)` | [CW]: ejes más relación **bajo un contexto**; el contexto es parte de la identidad |
| `L_i(C_i, R_i)`, índice semántico | ejes de símbolos `signo@ctx` del juego | las coordenadas son símbolos contextuales, nunca signos |
| `V_i`, `S_i`, `W_i* = V_i ⊙ S_i` | igual | no reciben ninguna cantidad estimada por frecuencias |
| `∅` (hecho no mapeado) | `UNKNOWN` | tercer valor de verdad |
| `(W_i ⊗ W_iᵀ) − I`, colisiones | igual dentro del juego; **configuraciones × símbolos** entre contextos | generalización de §5.1 |
| `D_i`, dimensión discriminante | candidato `D_i` de `maintain_wigame` | ordenado por la jerarquía de SIA, decidido por el álgebra |
| `C_k`, `WC_k`, compuertas y proyecciones de ruteo | candidatos `gate`, `RoutingProjection` | |
| `E(R) = ¼(c+i+o+d)`, mantenimiento | `maintain_wigame` | CHIC solo ordena candidatos |
| `aliases.yaml`: `(contexto, símbolo) → canonical` ([KH]) | referente `ref:k` y candidatos `equivalent` | la convergencia propone lo que [KH] cura a mano |
| `RoutingProjection` por referente compartido ([CW]) | candidato `projection`, direccional | la dirección sale de la asimetría de `ϕ` |
| compuerta de revisión `pending / approved / rejected` ([KH]) | `proposed / promoted / rejected` | la regla de promoción es un revisor determinista |
| hipertensor canónico `N × \|R\| × N` ([PP] apéndice) | no se materializa | §7 |

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
medida sobrestima la independencia de la evidencia (§12).

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

## Referencias

**Trabajo original (repositorio `jpcosec/Matrix`)**

- **[PP]** *Logical and Semantic Guarantees in LLMs Require More Than Continuous Embeddings.*
  Position paper. `paper_v2/build/paper.composed.md`. Secciones usadas: introducción, §2 fundamento
  filosófico, §3 representación propuesta, discusión, conclusión y apéndices (límites de la
  aproximación continua, columna formal, representaciones cerradas, omnirepresentación, camino de
  ingesta, auto-optimización `E(R)`, integración de la máscara de sentido).
- **[CW]** *WiGame, Context and Disambiguation.* `Matrix/docs/context_and_wigame.md`. Materializa los
  átomos `WiGame_Contexto_y_Desambiguacion`, `Contexto_Logico`,
  `Emergencia_Estructural_de_Si_en_Cruces_de_Contexto`, `Juego_de_Desambiguacion` y
  `Colapso_Dimensional`.
- **[LP]** *Pipeline de Ingesta: del lenguaje natural a matrices booleanas.*
  `Matrix/docs/language_to_matrix_pipeline.md`.
- **[KH]** *KB Fan-out Harness.* `Matrix/docs/kb_fanout_harness.md`, con las KBs versionadas
  `Matrix/examples/kb_wikipedia_10_articles/` y `Matrix/examples/kb_wikipedia_marie_curie/`
  (propuestas, revisión y `aliases.yaml`).

**Otras fuentes**

- Wittgenstein, L. *Tractatus Logico-Philosophicus* (1922).
- Gras, R., Suzuki, E., Guillet, F., Spagnolo, F. (eds.). *Statistical Implicative Analysis: Theory
  and Applications.* Springer, Studies in Computational Intelligence 127 (2008). Capítulos 1, 2 y 11.
- Winograd, T. *Procedures as a Representation for Data in a Computer Program for Understanding
  Natural Language* (SHRDLU). MIT AI TR-235 (1971).
- Webster, K., Recasens, M., Axelrod, V., Baldridge, J. *Mind the GAP: A Balanced Corpus of Gendered
  Ambiguous Pronouns.* TACL 6 (2018).
- Korel, `github.com/cognicore-io/korel`.
- Wikipedia en inglés y Simple English Wikipedia (CC BY-SA 4.0); Wikidata (CC0).

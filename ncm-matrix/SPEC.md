# Matrix–NCM: especificación del primer experimento conjunto

Estado: implementada en [`joint/`](joint/); diseño, decisiones y resultados en [`JOINT.md`](JOINT.md).
Versión: 0.1 — 23 de octubre de 2026.

Este documento fija decisiones para el siguiente experimento. Sustituye, para
ese experimento, las descripciones abiertas de la conversación y del draft.
Los valores numéricos son configuraciones iniciales, no resultados ni óptimos.

## 1. Objetivo y alcance

Aprender conjuntamente:

1. La representación de las ocurrencias textuales bajo contexto.
2. Su correspondencia con campos semánticos.
3. Las relaciones de ruteo entre contextos que permiten interpretarlas.

Las tres partes DEBEN recibir actualización desde el primer paso de entrenamiento.
No se permite entrenar primero una taxonomía definitiva, congelarla y llamar a
eso aprendizaje conjunto. Las pérdidas supervisan consecuencias observables;
no se proporciona un árbol objetivo como definición de la representación.

El primer experimento usa texto y RDF controlados, Matrix como evaluador y el
tokenizer VQ de NCM como base entrenable. No incorpora todavía el generador NCM,
extracción libre de RDF ni creación ilimitada de nodos. No demuestra por sí solo
una arquitectura de lenguaje general.

## 2. Unidad de datos

**Un registro es un fragmento con varias ocurrencias alineadas a proposiciones,
su contexto observable y las consultas que debe resolver.** Una ocurrencia es
un span; no tiene que coincidir con un token del tokenizer.

Esquema lógico de un registro:

```text
example_id: string
source_group: string                     # unidad para separar train/val/test
text: string
observed_context: list[(relation_uri, value_uri)]
mentions: list[{mention_id, start, end}]  # caracteres Unicode, [start,end)
queries: list[{
    query_id,
    subject: mention_id | resource_uri,
    relation: relation_uri,
    object: mention_id | resource_uri
}]
supervision: {
    reference_context_id: string,
    assertions: list[{
        query_id,
        truth: true | false | unknown,
        applicable: true | false | unknown,
        provenance: {source_id, span, method}
    }],
    identity_constraints: list[{
        first_mention, second_mention,
        relation: same_referent | distinct_referent,
        scope: string
    }],
    rules: list[{formula, scope, provenance}]
}
```

Ejemplo de contenido: «El banco rechazó la solicitud de crédito», con spans para
«banco» y «solicitud de crédito», una consulta relacional y metadatos realmente
disponibles en la tarea. Los triples son objetivos alineados, no una segunda
entrada que revele las respuestas.

Reglas del contrato:

- `supervision` sólo entra al evaluador y a las pérdidas. No entra al encoder.
- `reference_context_id` identifica el mundo del oráculo; no es el ID de un Wi
  aprendido ni se entrega al router como respuesta.
- Los IDs de fuente, ejemplo y consulta no son features neuronales.
- Contexto ausente se representa como ausente, no se rellena con etiquetas de test.
- No se interpreta ausencia de triple como falsedad o inaplicabilidad.
- Las URIs se preservan completas. Se registran las alineaciones carácter/token.
- El loader rechaza spans inválidos y fragmentos demasiado largos; no trunca
  silenciosamente evidencia o consultas.

Los pares contrafácticos de un mismo fragmento se incluyen juntos en minibatches.
Todas sus variantes pertenecen a la misma partición del dataset.

## 3. Qué se almacena y qué se aprende

### 3.1 Estado compartido

La versión inicial tiene un banco finito de **slots**: posiciones de parámetros
sin etiqueta semántica predeterminada. Un slot no es automáticamente un concepto.

| Estado | Forma inicial | Significado |
|---|---|---|
| Parámetros del encoder/adaptador | según NCM | Representación contextual |
| Prototipos de campo `F` | `[64, 64]` | Candidatos latentes compartidos |
| Descriptores de Wi `U` | `[32, 64]` | Contextos/juegos candidatos compartidos |
| Mapeo de Wi a perfiles `A` | `[32, C]` | Logits sobre combinaciones de restricciones observables |
| Representaciones de relaciones | `[R, 64]` | Relaciones observadas y meta-relaciones |
| Cuantizador multiescala | 3 niveles | Códigos de reconstrucción |
| Evaluador neuronal de proposiciones | parámetros compartidos | Scores de verdad/aplicabilidad y rutas |

`F` y `U` se aprenden. Sus índices son estables dentro del checkpoint, pero
permutables semánticamente: slot 7 no significa «animal». Una región se interpreta
por sus correspondencias y relaciones verificadas, no por el nombre de su slot.

Un campo puede participar en distintos Wi. Un Wi puede recibir varias rutas.
La estructura compartida es un grafo; no se duplican todos los campos para
materializar cada combinación de país, tema, registro y función retórica.

`C` es el conjunto finito de perfiles de restricciones admitidos por el fixture,
enumerado a partir del esquema y valores de train, no de ejemplos de test. Un
perfil es una conjunción parcial de atributos observables. No contiene campos
objetivo ni padres/hijos. `softmax(A)` aprende qué perfiles describe cada Wi;
no se asigna un perfil fijo a cada slot. Esta versión aprende su combinación y
organización, no descubre desde cero el significado de los atributos anotados.

### 3.2 Ruteo como proposiciones

Los Wi son también endpoints reificados. Una ruta se representa como
`(routes_to, wi_i, wi_j)` bajo un Wi de ruteo. Un evaluador neuronal compartido
puntúa esa proposición, igual que puntúa otras relaciones, usando el contexto
del ejemplo. Se permiten proyecciones de rol para endpoints de tipos distintos.

La implementación NO debe añadir un árbol externo con decisiones inconexas de
las proposiciones de Matrix. Debe existir un adaptador explícito entre las rutas
predichas, su representación como proposiciones y las rutas ejecutadas.

El contexto de entrada es un punto de arranque computacional, no la raíz de una
ontología universal. Los candidatos de ruta abarcan todos los Wi en esta versión.
No hay recuperación ANN ni poda top-k durante entrenamiento.

### 3.3 Estado por ejemplo

| Tensor | Forma | Significado |
|---|---|---|
| `H` | `[batch, length, 64]` | Representaciones de tokens |
| `h` | `[mentions, 64]` | Agregación de spans |
| `w` | `[mentions, 32]` | Distribución de acceso a Wi |
| `m` | `[mentions, 64]` | Distribución sobre campos |
| `P_route` | `[mentions, 32, 32]` | Transiciones contextuales candidatas |
| `truth`, `sense` | `[queries]` | Probabilidades de verdad y aplicabilidad |

`m` depende del contexto de la ocurrencia. No es una tabla palabra→campo.
`H`, `w` y `m` son activaciones; `F` y `U` son parámetros compartidos.

## 4. Forward: dependencia mutua sin ciclo indefinido

Se ejecutan exactamente **dos pasos de refinamiento** en la primera versión.
Todos pertenecen a un único grafo de autograd, sin detach intermedio.

1. Codificar texto y contexto observable en `H0`.
2. Agregar los spans y producir `m0` mediante compatibilidad con `F`.
3. Inicializar `w0` con una distribución aprendida desde esa evidencia. Se usa
   el mismo scorer de rutas, con un endpoint de entrada explícito.
4. Para cada paso `t = 0,1`:
   - Puntuar `(routes_to, wi_i, wi_j)` condicionado por `H_t`, `m_t` y el
     contexto observable; normalizar por destino para obtener `P_route_t`.
   - Propagar `w_next[j] = sum_i w_t[i] * P_route_t[i,j]`.
   - Formar el descriptor de cada Wi como `U[j] + sum_c softmax(A[j])[c] * E[c]`,
     donde `E[c]` codifica las restricciones del perfil con parámetros aprendidos.
     Obtener `u` como promedio de esos descriptores ponderado por `w_next`.
   - Actualizar `H_next` desde `H0`, `u` y el campo esperado `m_t @ F`.
     Las contribuciones de spans solapados se promedian; fuera de spans se usa
     el contexto agregado del fragmento.
   - Recalcular `m_next` desde los nuevos spans y `u`.
5. Cuantizar la representación final con VQ multiescala.
6. Reconstruir texto y recalcular el mapeo final desde los spans cuantizados.
7. Puntuar las consultas desde las distribuciones de campo finales y `w`.

Las cabezas de consultas no reciben texto o etiquetas por un canal adicional
que evite la representación cuantizada. El contexto aprendido sí forma parte
de su entrada, a través de `w`.

La implementación inicial usa MLPs de dos capas con GELU y softmax para mapeo y
ruteo. La cabeza de proposiciones recibe las representaciones esperadas de ambos
endpoints (`m @ F`, o el embedding de una URI constante), la relación y el
descriptor contextual. Produce logits separados de verdad y aplicabilidad. La
cabeza de rutas usa esa misma función con endpoints Wi reificados. Los logits de
verdad sobre destinos admisibles se normalizan para obtener transiciones; una
auto-ruta garantiza salida. La máscara de endpoints es estructural, no depende
de la aplicabilidad predicha.

Los codebooks se actualizan por el mecanismo EMA de NCM una vez por forward
de entrenamiento. Encoder, `F`, `U`, mapeo y scorer reciben gradiente; no se
afirma que EMA sea una actualización por Adam. La selección VQ usa su estimador
straight-through. No se usan helpers de inferencia bajo `no_grad`.

Los tres niveles VQ NO son tres niveles ontológicos. Los dos pasos de refinamiento
tampoco son una profundidad semántica universal. Son presupuestos de cálculo
fijados para probar el mecanismo.

## 5. Matrix: contrato del oráculo

Habrá dos espacios separados:

- **Referencia:** hechos, contextos y restricciones del dataset, inmutables.
- **Predicción:** interpretaciones y rutas propuestas por el modelo.

El oráculo retorna por consulta `truth`, `applicable`, `discriminative`,
`truth_known`, `sense_known` y procedencia. Las consultas se evalúan sobre los
mismos endpoints observados en todas las alternativas. Cambiar de ruta no puede
borrar una obligación supervisada.

La identidad de referentes del dataset es un anclaje, no un ID de slot. Se
supervisa con restricciones de correspondencia contextual; el modelo puede
distribuir sus campos de maneras equivalentes si preserva esas restricciones.

El adaptador DEBE resolver antes de entrenar las discrepancias ya reproducidas:
bitmask que activa cadenas `false/unknown`, pérdida de máscaras locales en
bloques y aserciones que sobrescriben `unsinnig`. No se evalúan predicciones
insertándolas mediante `assert` en la referencia. `accept` no es una etiqueta
de verdad. `sinnlos` no se etiqueta como inaplicable.

La implementación inicial puede evitar esas rutas defectuosas mediante lecturas
explícitas y el evaluador de fórmulas verificado. Debe tener pruebas del contrato;
no necesita modificar todo Matrix para comenzar.

## 6. ASI: entrada, actualización y salida

ASI es una actualización estadística periódica dentro del entrenamiento conjunto.
**No recibe gradiente en esta versión.** Tampoco produce etiquetas de verdad.

Cada 250 pasos se construye una instantánea usando hasta 4096 registros de train,
seleccionados por un reservorio reproducible. Se vuelven a codificar todos con
el checkpoint actual en modo evaluación, sin actualizar EMA. No se mezclan
asignaciones antiguas de distintos checkpoints en la misma matriz.

Se calculan tres vistas:

| Vista | Individuos × variables | Uso |
|---|---|---|
| Contextos | Fragmentos/contextos observados × configuraciones relacionales | Proponer agrupaciones y acceso entre Wi |
| Correspondencias | Configuraciones × símbolos/ocurrencias agrupadas por asignación actual | Proponer proyecciones entre campos |
| Discriminación | Sujetos × coordenadas observadas de un mundo local | Detectar compuertas y colisiones |

Las asignaciones neuronales se discretizan sólo para esta instantánea. Cada
variable mantiene su correspondencia con slots y observaciones. Las
configuraciones combinan relaciones observadas con las interpretaciones actuales;
el modelo no puede cambiar qué triple fue observado.

ASI trabaja con incidencias binarias. Un cero significa que una configuración
no está presente en la representación observada de esa unidad, no que una
proposición del mundo sea falsa. Se excluyen de cada análisis unidades con
observación incompleta para las variables comparadas. Se registran universo,
soporte, contraejemplos y política de máscara.

La salida es una lista versionada de propuestas:

```text
kind: route | projection | gate | discriminant
source, target: slot_id | observed_feature_id
score: implicative_intensity
support, counterexamples, universe_size: integers
snapshot_step: integer
status: proposed | eligible | rejected
reason: string
```

Reglas:

- Intensidad implicativa no es probabilidad de verdad ni identidad lógica.
- Reciprocidad genera un candidato a equivalencia; no fusiona automáticamente
  referentes ni hechos.
- `gate` y `discriminant` indican evidencia para reorganizar; no crean una
  dimensión aprendida simplemente por recibir un nombre.
- No se eliminan campos ni se cambian sus IDs durante esta versión.
- Las propuestas actualizan comparaciones supervisadas entre candidatos; nunca
  fijan sus vectores ni congelan las rutas.

Puente inicial hacia autograd: ranking de candidatos. Si dos propuestas comparten
origen y universo comparable y sus intensidades difieren al menos en 0.1, el
scorer neuronal debe ordenar sus destinos en el mismo sentido. Usar margen 0.2
sobre scores sigmoid, normalizar por comparaciones y omitir universos sin soporte.
Esto se llama `L_ASI`; no se presenta como ASI diferenciable. El umbral inicial
de soporte es 20 unidades observadas; si no se alcanza, el término vale cero y
se reporta que ASI no aportó supervisión.

## 7. Pérdidas y actualización conjunta

```text
L = L_reconstruction + L_VQ
  + L_truth + L_sense + L_correspondence
  + 0.2 * L_logic + 0.1 * L_ASI + 0.01 * L_route_cost
```

Cada término se promedia sobre sus elementos válidos. Un conjunto vacío produce
cero y un contador visible, nunca NaN. Los pesos son un punto inicial configurable.

| Término | Definición y límite |
|---|---|
| Reconstrucción | CE de tokens no padding; preserva contenido lingüístico |
| VQ | Pérdida del cuantizador NCM y su actualización EMA |
| Verdad | BCE sólo para verdad conocida y aplicabilidad de referencia positiva |
| Sentido | BCE sólo donde existe etiqueta de aplicabilidad de referencia |
| Correspondencia | Contraste sobre pares de ocurrencias con identidad/distinción anotada bajo el mismo alcance; compara sus distribuciones de campo |
| Lógica | Masa de asignaciones inválidas para fórmulas pequeñas sobre átomos distintos, con ámbito aplicable verificado |
| ASI | Ranking estadístico descrito en §6 |
| Coste de ruta | Coste esperado de cruces inaplicables bajo las rutas, medido sobre el conjunto fijo de consultas; no cuenta desconocidos como inaplicables |

Para correspondencia: similitud inicial `m_a dot m_b`, BCE con etiqueta same/distinct
y clipping numérico. Se equilibran pares positivos/negativos y se informa colapso.
Esta restricción es una decisión del experimento, no una definición universal
de campo semántico. Si un par admite varias interpretaciones, no se etiqueta
forzosamente como same/distinct.

Para coste de ruta: el fixture proporciona una tabla `cost[query, profile]`
de cruces explícitamente inaplicables y una máscara de costes conocidos. Se
promedia esa tabla usando `w @ softmax(A)`, sólo sobre entradas conocidas. La
masa asignada a costes desconocidos se informa separadamente y no cuenta como
coste cero en las comparaciones. Así se aprende tanto el acceso a Wi como su
interpretación en términos de restricciones. Verdad, sentido y correspondencia
siguen supervisadas aunque un coste sea desconocido. No se afirma minimizar
memoria global, entropía total ni tamaño del grafo.

**Ninguna máscara de pérdida proviene de la predicción de sentido.** El modelo
no puede evitar una obligación prediciendo `unsinnig`. El scorer de verdad se
entrena con los mismos targets independientemente de la ruta seleccionada.

```python
for step, batch in enumerate(train_loader):
    prediction = model(batch.inputs, refinement_steps=2)
    targets = reference.evaluate(batch.supervision)   # sin mutar referencia
    loss = losses(prediction, targets, asi_snapshot)
    optimizer.zero_grad()
    loss.backward()                                 # todas las partes neuronales
    optimizer.step()
    if (step + 1) % 250 == 0:
        asi_snapshot = rebuild_asi(model, train_reservoir)
```

No se congelan encoder, mapeo o ruteo para esperar a ASI. Cuando no hay propuestas
ASI válidas, siguen aprendiendo por las otras pérdidas.

## 8. Datos mínimos para distinguir éxito de memorización

El fixture siguiente DEBE contener:

1. El mismo signo con referentes diferentes según contexto.
2. Signos distintos que convergen en un referente bajo un alcance anotado.
3. Al menos tres dimensiones contextuales cruzadas, con combinaciones reservadas
   para test; no basta una etiqueta binaria de contexto.
4. Proposiciones verdaderas, falsas, desconocidas y explícitamente inaplicables.
5. Dos organizaciones alternativas que conservan los hechos, pero difieren en
   cruces inaplicables bajo consultas idénticas.
6. Casos donde un rasgo universal no discrimina y otros donde sí discrimina.
7. Evidencia suficiente para que al menos una actualización ASI tenga soporte.

Las combinaciones de test se fijan antes de entrenar. ASI, vocabulario y propuestas
usan sólo train. Las métricas por entidad nueva se separan de las métricas por
combinación contextual nueva. El fixture actual botánica/fábula no cumple este
contrato y se conserva únicamente como prueba previa.

## 9. Pruebas y criterios de aceptación

### 9.1 Aceptación de implementación

- Un minibatch produce gradientes finitos y no nulos en encoder, prototipos de
  campo, descriptores Wi y scorer de rutas. Se comprueba también una contribución
  de tarea a rutas, no sólo el gradiente de una regularización auxiliar.
- Cambiar una ruta altera representación y correspondencia en un ejemplo diseñado
  para requerir contexto. Hay gradiente a través de ambos pasos de refinamiento.
- Las rutas ejecutadas y las proposiciones `routes_to` exportadas coinciden.
- El evaluador distingue unknown, false, unsinnig y sinnlos sin mutar la referencia.
- El coste se compara sobre las mismas consultas. Marcar todo inaplicable no
  elimina pérdidas ni mejora artificialmente cobertura.
- Dos instantáneas ASI con asignaciones distintas reconstruyen sus configuraciones;
  no reutilizan una taxonomía inicial congelada.
- Permutar conjuntamente slots y referencias no cambia las salidas.
- Un checkpoint guarda parámetros, EMA, optimizador, reservorio, propuestas ASI,
  vocabulario, configuración y RNG; permite reanudar el siguiente paso.

### 9.2 Evaluación científica

Tres semillas: 7, 19 y 41. Mismo presupuesto de pasos para comparar:

1. Modelo conjunto completo.
2. Sin ASI.
3. Ruteo congelado desde inicialización.
4. Sin contexto.
5. Sin pérdida lógica.

Reportar correspondencia, verdad conocida/aplicable, aplicabilidad, violaciones
lógicas discretas, reconstrucción, cobertura, coste de ruta, ocupación de slots
y diferencias entre semillas. Medir por separado combinaciones vistas/no vistas.
También registrar propuestas ASI elegibles y cambios efectivos de rutas.

La hipótesis de aprendizaje conjunto recibe apoyo sólo si mejora la tarea bajo
contextos reservados y supera las ablaciones relevantes sin perder cobertura.
Gradientes no nulos, códigos diferentes o 100% en train no bastan. No se fija una
mejora numérica garantizada antes de ejecutar el experimento.

## 10. Presupuesto, entregables y exclusiones

Configuración inicial: 64 tokens por fragmento, dimensión 64, 64 campos candidatos,
32 Wi candidatos, 2 refinamientos, minibatch de 8 fragmentos; VQ con longitudes
16/32/64 y 32 entradas por codebook. La compatibilidad de estas dimensiones debe
verificarse contra el tokenizer clonado. Reducir batch si la memoria lo exige;
registrar el cambio. No se afirma de antemano que quepa en una GPU concreta.

En este tamaño se evalúan todos los candidatos. Su coste incluye términos
cuadráticos en el número de Wi; **no es todavía un diseño escalable a un árbol
gigante**. Retrieval, poda y crecimiento de capacidad quedan fuera hasta demostrar
que el aprendizaje conjunto funciona en el caso exhaustivo.

Entregables (implementados; ver `JOINT.md`):

```text
joint/schema.py           validación y separación inputs/targets
joint/fixture.py          dataset contextual cruzado
joint/model.py            forward conjunto y VQ
joint/matrix_adapter.py   contrato de referencia y exportación de rutas
joint/asi_adapter.py      instantáneas, estadísticas y ranking
joint/train.py            trainer y checkpoints
joint/evaluate.py         métricas y ablaciones
joint/tests/              contratos anteriores
```

No son parte de esta versión: crecimiento/fusión irreversible de nodos,
descubrimiento abierto de nuevas relaciones, RDF desde prosa libre, generador
NCM completo, aprendizaje en test y equivalencia entre código VQ y concepto.

## 11. Autoridad y dependencias

- Implementación Matrix oficial: `../Matrix/Matrix`.
- NCM clonado: `ncm/`, commit documentado en `ANALISIS.md`.
- Estado y discrepancias del oficial: `REVISION_MATRIX.md` y
  `artifacts/matrix_contract_audit.json`.
- El oficial referencia SIA/CHIC en `docs/semantic_fields.md` y `PORT_GAPS.md`.
  Su implementación inspeccionada está en `../matrix-shrdlu-spec/sia/` y
  `pipeline/convergence.py`; eso no convierte ese árbol en Matrix oficial.

El adaptador ASI debe aislar las rutinas numéricas de las APIs del runtime externo.
No importar su `pipeline` como si fuese compatible con el oficial. Antes de usar
esas rutinas se fijan revisión, licencia, dtype de conteos y tests de referencia;
los conteos deben evitar overflow de matrices binarias almacenadas como int8.

El paper versión 0.1 no describe todavía este forward ni el contrato ASI. Este
spec no presenta esas extensiones como resultados ya medidos.

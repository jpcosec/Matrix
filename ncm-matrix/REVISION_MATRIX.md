# Revisión de Matrix: representación contextual y aprendizaje

Revisión del 23 de octubre de 2026. Implementación de referencia:
`../Matrix/Matrix`, árbol de trabajo existente, no solamente su commit HEAD.
No se modificó su código. `matrix-shrdlu-spec` no se usa como autoridad.

Se revisaron arquitectura, Whitepaper, documentación operacional, núcleo de
representación, matrices, kernel, deducción, ruteo, reflexión, partición,
ingestión KB, formatos externos, ejemplos y pruebas. Se contrastaron también
los fundamentos de `../Matrix/TractatusKnowledgeMachine/atoms` y `../Matrix/paper_v2`.
Es una revisión transversal con comprobaciones ejecutables, no una verificación
formal ni la afirmación de haber inspeccionado cada línea de cada archivo.

## De dónde sale la propuesta

### 1. El objetivo es el campo semántico de una ocurrencia

La distinción signo/símbolo del Whitepaper y los átomos filosóficos separa
la forma perceptible de su función lógica contextual. El documento oficial
[`context_and_wigame.md`](../docs/context_and_wigame.md) lo dice
explícitamente: importa el campo semántico que indica la ocurrencia, y el
referente es la intersección que sobrevive a las restricciones contextuales.

Por tanto, predecir un ID VQ que reconstruye texto no demuestra que se prediga
ese campo. Hace falta una correspondencia comprobable entre ocurrencias,
campos y relaciones bajo contexto. Un mismo signo puede indicar campos distintos;
signos distintos pueden converger en el mismo referente bajo restricciones.

### 2. El contexto reúne dimensiones transversales

País, registro, tema y función retórica pueden expresarse como relaciones y
restricciones, sin convertirlas en un único árbol taxonómico universal.
`LiSpace` fija ejes y relación; `WiGame` añade estado y contexto. La reflexión
reifica relaciones y contextos como símbolos: véanse
[`reflection.py`](../src/operational_model/system/reflection.py)
y sus tests de habla informal/chileno.

Esto proporciona piezas representacionales. No hay un extractor general que
descubra automáticamente todas esas dimensiones en textos, ni un predictor
entrenado de sus combinaciones. El prototipo adjunto sólo usa dos IDs de contexto.

### 3. La jerarquía pertenece a la organización contextual

El Whitepaper y `paper_v2/sections/03_proposed_representation.md` desarrollan
factorización, reorganización de dimensiones y espacios que indexan otros
espacios. La jerarquía de navegación no tiene por qué ser una ontología intrínseca
del grafo de hechos. La documentación operacional actual sí describe un árbol
de `Context` hacia hojas `WiGame`: es una organización concreta del acceso.

El ejemplo de perros bajo frutas señala un coste de representación: cruces
inaplicables y dimensiones que no discriminan en ese contexto. Eso motiva
aprender una organización útil; no autoriza a marcar como falsos los datos
ausentes ni a minimizar indiscriminadamente la entropía de toda distribución.
Una pregunta que divide candidatos equilibradamente puede ser muy informativa.

[`partition.py`](../src/operational_model/system/partition.py)
ya compara un mundo compuesto con una partición suministrada. Mide celdas,
densidad, energía y columnas tautológicas; decide principalmente por coste de
celdas y reutilización del término medio. **No busca particiones nuevas ni
aprende una jerarquía**, y no implementa una pérdida explícita por todos los
don't-cares. La discriminación se calcula; no hay que presuponer una matriz
`D_i` universal entrenable equivalente a `Vi` y `Si`.

### 4. El ruteo también puede ser conocimiento

El átomo `Ruteo_Como_Relacion` formula exactamente esa intención: contextos y
juegos como símbolos, y ruteo como relaciones. Parte de ese texto aún describe
un hipertensor canónico global que la documentación operacional actual declara
abandonado. Debe conservarse el principio sin atribuirle ese backend al runtime.

Hoy hay `Context`, rutas explícitas, `RoutingProjection`, composición por término
medio y reflexión. Además,
[`operatoria.py`](../tools/kb/operatoria.py) materializa reglas
operacionales como un contexto consultable. Es un ejemplo concreto de conocimiento
sobre cómo operar representado dentro del sistema.

Pero las rutas siguen registradas en estructuras dedicadas; reificar un contexto
no sincroniza automáticamente sus rutas con hechos de otro Wi. Tampoco existe
un entrenamiento que descubra esos Wi de ruteo. **La autorreferencia tiene soporte
parcial; el aprendizaje del ruteo no está implementado.**

## Estado del flujo de datos

El pipeline oficial `tools/kb` ingiere propuestas, conserva procedencia y
revisión, compila mundos por contexto/relación y construye proyecciones.
La organización por fuentes está programada: no constituye aprendizaje de
país, género discursivo, tema o función retórica.

Hay dos rutas OWL distintas. El importador de `operational_model/language` es
limitado, pero **sí existe soporte Turtle** en
[`external_formats/owl/owl_converter.py`](../src/external_formats/owl/owl_converter.py)
mediante rdflib. Convierte clases, individuos y propiedades a s-expressions.
Eso no equivale a compilar cualquier RDF en contextos lógicos ejecutables:
el ejemplo mínimo genera una aserción a `wigame:owl` sin crear ese mundo.
También debe preservarse la identidad completa de URIs al integrar datos reales.

UNL aporta conversión de relaciones y atributos; no demuestra extracción fiable
de estructura lógica desde lenguaje natural arbitrario. Un dataset RDF-texto
necesitará además alineación de ocurrencias, contextos, negación, modalidad y
procedencia. Las dimensiones ausentes del dataset requerirán anotación o
extracción evaluada por separado.

## Verificación y discrepancias reproducibles

Suite completa del repositorio oficial: **274 passed in 4.63s**. Se ejecutó con
`python3 -m pytest -q -p no:cacheprovider`, sin bytecode, dentro de un scope con
MemoryMax=4G y MemorySwapMax=0. Los tests externos de pi/Ollama no se ejecutaron.
Una suite verde no prueba todas las propiedades descritas en los documentos.

Se añadió [`audit_matrix_contract.py`](audit_matrix_contract.py), que construye
mundos efímeros sin modificar el repo oficial. Ejecutar desde esta carpeta:

```bash
python3 audit_matrix_contract.py
```

Resultados guardados en
[`artifacts/matrix_contract_audit.json`](artifacts/matrix_contract_audit.json):

| Comprobación | Resultado observado | Consecuencia para entrenamiento |
|---|---|---|
| Bitmask de Vi con `true,false,∅` | `7`, activa los tres bits | No usar esa conversión como máscara de verdad sin corregir su contrato; sólo true daría `1`. |
| `check` dirigido a una celda `unsinnig` | `accept` con sentido `unsinnig` | `accept` no significa aplicabilidad ni verdad. |
| `assert` dirigido sobre esa celda desconocida | Cambia a `true/sinnvoll` | La aserción puede sobrescribir la máscara; no usarla como evaluación inmutable de predicciones. |
| Celda local verdadera marcada `unsinnig`, ensamblada en bloque | Local no aplicable, evaluación del bloque `true` | La composición no conserva esta máscara local; escoger y validar una semántica de evaluación. |
| Turtle mínimo convertido y ejecutado en sistema vacío | Crea símbolos, rechaza la aserción | Falta construir el Wi y su contrato para completar la ingestión. |
| Exportación de `(assert wigame:w (r a b))` | Cero triples | El round-trip de una aserción canónica no funciona en esta prueba. |

Son observaciones concretas, no una afirmación de que todo el kernel falle.
Por ejemplo, la resolución sin selector de Wi no sigue necesariamente la misma
ruta que un `assert` dirigido. Las operaciones que comparan explícitamente con
`TruthValue.TRUE` no heredan por ello el error de conversión a bitmask.

La prueba también registra una limitación de **nuestro** dataset: guardaba
`context_id` en `metadata` pero dejaba vacío el campo real `WiGame.context_id`.
La comparación neuronal seguía condicionada y los sistemas estaban separados,
pero eso no ejercitaba el grafo oficial de contextos. No se ha corregido
silenciosamente ni presentado ese resultado como integración completa.

## Qué cambia para Matrix × NCM

El experimento existente prueba que una señal contextual puede modificar la
representación cuantizada y permitir distinguir respuestas bajo dos contextos.
No prueba los cuatro requisitos anteriores. No aprende campos como objetivos
explícitos, dimensiones transversales ni Wi de navegación; tampoco utiliza el
generador NCM. Sus métricas sintéticas no justifican una estimación del coste de
entrenar la arquitectura completa.

Una formulación futura coherente sería predecir conjuntamente una organización
contextual y el campo de la ocurrencia, condicionados por el texto disponible:

```
ocurrencia + contexto discursivo disponible
    → propuestas de dimensiones / Wi / relaciones de ruteo
    → campo semántico condicionado por esas elecciones
    → evaluación de sentido, verdad y discriminación en Matrix
```

Es una propuesta de interfaz, no una factorización probabilística ya implementada.
Los niveles coarse-to-fine de NCM no son por definición padre/hijo ontológicos:
hay que aprender su correspondencia con refinamientos de campos y decisiones de
ruteo. Las cabezas pueden puntuar candidatos simbólicos; las elecciones discretas
requieren un estimador/relajación explícito si se quiere entrenar por gradiente.

La supervisión debe separar: grounding de ocurrencias; restricciones de verdad;
aplicabilidad contextual; calidad/coste de la organización. La lógica exacta de
Matrix puede producir etiquetas, restricciones y métricas; no se convierte en
diferenciable por añadir su resultado al loss. Tampoco `sinnlos` es sinónimo de
contradicción: la falta de discriminación sirve para evaluar una partición, no
para declarar falsas todas sus proposiciones.

El siguiente ensayo representativo necesitaría casos con el mismo signo en
contextos cruzados, particiones alternativas del mismo grafo, rutas reificadas
como proposiciones y evaluación sobre combinaciones no vistas. Tendría que
penalizar una partición llena de cruces inaplicables sin permitir la solución
trivial de declarar todo inaplicable. Eso requiere cobertura y reconstrucción
además de regularización lógica. Aún no está construido en este directorio.

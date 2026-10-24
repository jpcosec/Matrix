# Auditoría de integración Matrix × NCM

Revisión local del 22 de octubre de 2026. NCM:
`c70274273f489abc73832b2b98584a8483b6b203`. Matrix se leyó desde el árbol de trabajo
`../Matrix/Matrix`, con HEAD `f016c75e8af3aedd7b46fa4a984706802382afaf` y cambios
locales preexistentes. Por tanto ese hash no identifica por sí solo todo el código
Matrix evaluado. **Corrección del 23 de octubre:** `matrix-shrdlu-spec` no es
la implementación oficial y no debe usarse como autoridad arquitectónica.
La revisión ampliada del oficial y sus fundamentos está en
[`REVISION_MATRIX.md`](REVISION_MATRIX.md), con discrepancias reproducibles.

## Qué permite realmente NCM

- [`models/vqvae.py`](ncm/models/vqvae.py): `forward()` tiene ruta entrenable:
  `_encode_pre_quant → vq → decoder`. `encode`, `encode_z`, `decode` y
  `get_ncm_inputs` están decorados con `no_grad`. Usarlos directamente para una
  pérdida de Matrix cortaría la ruta de gradiente deseada.
- [`models/quant.py`](ncm/models/quant.py): selección discreta por `argmin`;
  codebooks con `requires_grad=False`, actualizados por EMA durante training;
  salida `z + (z_hat - z).detach()` como straight-through. Añadir una pérdida
  a la salida puede mover el encoder, y los codebooks lo siguen por EMA;
  no significa optimizar directamente sus vectores con Adam.
- [`models/vae.py`](ncm/models/vae.py): el encoder por defecto tiene cero bloques
  de atención, embeddings de tokens/posición y dropout. En TinyStories el config
  no activa capas de encoder. El parámetro `n_layers: 6` del tokenizer sirve como
  número de heads, no como seis capas de encoder. No se debe presuponer que `z`
  ya representa por sí mismo `P(campo semántico | contexto)`.
- [`config/eval/tinystories.yaml`](ncm/config/eval/tinystories.yaml): 128 tokens,
  dimensión 384, 12 niveles, cada codebook de 4096 entradas. El generador tiene
  12 capas y dimensión 768. Estas son dimensiones distintas de las del smoke test.
- [`models/next_concept.py`](ncm/models/next_concept.py): `forward()` devuelve
  logits por nivel y puede utilizarse para un trainer nuevo. `generate()` está
  bajo `no_grad`. Las cabezas ligadas a codebooks guardan copias desacopladas;
  si cambia el tokenizer, hay que revisar esas copias y recodificar los targets.

El release publica rutas forward entrenables, pero no un pipeline completo de
reentrenamiento. Tampoco basta quitar un decorador: hay `detach`, asignaciones
discretas, EMA y dependencias tokenizer/generador que requieren diseño explícito.
Se observó además que `VQVAE.reconstruct()` desempaqueta tres valores de un
cuantizador que devuelve cinco; no lo usa este experimento ni se modificó upstream.

## Qué significa la evaluación de Matrix

- [`get_status`](../Matrix/Matrix/src/operational_model/system/wi_game_queries.py)
  trata fuera-de-ejes y `Si=unsinnig` como no aplicables. Una columna de Vi verdadera
  para todos los sujetos produce `sinnlos` y `discriminative=False`. Esa propiedad
  depende del mundo finito, no equivale a una contradicción lógica.
- [`_eval_check`](../Matrix/Matrix/src/operational_model/system/s_expression_runtime.py)
  comprueba encaje y devuelve el `Si` almacenado. Su `accept` no certifica verdad
  ni implica que `Si` no sea `unsinnig`; también usa `unsinnig` para ambigüedad o
  mundo inexistente. `_eval_assert` identifica una celda falsa como
  `widerspruechlich` al intentar afirmar verdad encima. No conviene entrenar sobre
  una sola cadena de estado sin su razón y contexto.
- [`ViMatrix`](../Matrix/Matrix/src/operational_model/matrices/vi_matrix.py)
  comienza en `∅`; [`SiMatrix`](../Matrix/Matrix/src/operational_model/matrices/si_matrix.py)
  comienza en `sinnlos`. Ausencia de evidencia no es falsedad ni inaplicabilidad.
- [`deduce`](../Matrix/Matrix/src/operational_model/system/deduction.py) hace
  deducción trazada de hechos verdaderos. Omite celdas ya verdaderas o falsas;
  no es un detector completo de inconsistencias. Para supervisar restricciones
  hay que conservar las fórmulas, evaluar asignaciones y distinguir contradicción
  con la KB de falsedad admisible en una proposición.
- [`formula_evaluation.py`](../Matrix/Matrix/src/operational_model/kernel/formula_evaluation.py)
  ofrece evaluación booleana y clasificación por enumeración. Es exacta para sus
  fórmulas, pero la enumeración de n átomos es exponencial. No escalarla ciegamente
  a toda la KB; compilar o muestrear restricciones locales sería otro trabajo.
- [`RoutingProjection`](../Matrix/Matrix/src/operational_model/routing/routing_projection.py)
  implementa enlaces booleanos explícitos. La similitud entre embeddings no
  autoriza por sí sola identidad entre símbolos de contextos distintos.

El experimento conserva dos decisiones separadas: plausibilidad de verdad y
aplicabilidad bajo Wi. `sinnlos` sigue siendo aplicable; D_i puede orientar
discriminación/partición pero no se usa como penalización universal de falsedad.

## RDF y procedencia

El [`owl2matrix.py`](../Matrix/Matrix/src/operational_model/language/owl2matrix.py)
existente es un importador XML limitado. No es un parser Turtle general; el código
omite `rdf:type` y `subClassOf` al recorrer hijos y no llena `subclass_relations`
en esa ruta. Su exportador crea un solo Li con la primera relación, lo que tampoco
resuelve un grafo multirrelacional arbitrario.

Por eso el experimento usa rdflib y un contrato RDF de aserciones explícito.
No se apoya en ese importador como si ya ofreciera inferencia OWL/RDFS completa.
El pipeline oficial `../Matrix/Matrix/tools/kb` agrupa mundos por contexto y
relación. Además del importador anterior existe
`../Matrix/Matrix/src/external_formats/owl/owl_converter.py`, que sí lee Turtle
mediante rdflib. Su salida no construye por sí sola los mundos necesarios para
ejecutar todas las aserciones; la revisión ampliada documenta pruebas de importación
y exportación. La evaluación inicial del soporte RDF fue incompleta.

Un corpus real necesitará vincular spans con proposiciones, preservar negación,
fuente, modalidad, contexto y confianza, y separar errores del extractor de
violaciones reales. Los negativos de sentido necesitan evidencia local: no salen
automáticamente de triples ausentes ni de dominios/rangos RDF interpretados como
restricciones cerradas. No se debe evaluar contra un oráculo reescrito con las
mismas predicciones que intenta juzgar.

## Reentrenamiento propuesto

```text
texto, Wi → encoder + condicionamiento → VQ multiescala → reconstrucción
                                  │
                                  └→ readout contextual de proposiciones
                                        │
texto/fuentes → RDF contextual → Matrix ─┤
                                  verdad, aplicabilidad, reglas
                                        │
                                  pérdidas diferenciables
                                        │
                                  encoder + adaptador
```

El código adjunto materializa este puente en pequeño. Entrena la representación,
no solamente un clasificador sobre features congeladas. La cabeza observa los
latentes cuantizados y la pérdida vuelve al encoder. Para textos generales, el
readout debe alinear entidades/relaciones/spans y no quedarse en siete predicados.

La relajación de implicación implementada tiene interpretación exacta sólo bajo
el modelo de dos Bernoulli independientes. Para fórmulas generales con átomos
repetidos, usar una probabilidad compartida por átomo y sumar masas sobre
asignaciones satisfactorias, o declarar otra relajación; multiplicar subfórmulas
como si todas fueran independientes puede incluso romper tautologías.

Una pérdida blanda baja no garantiza que toda generación satisfaga Matrix.
Las métricas del kernel sobre salidas discretas siguen siendo necesarias.
También hacen falta ablations de pérdidas y reconstrucción para descartar que el
modelo sólo aprenda una cabeza conveniente o soluciones lógicas vacías.

Para aprovechar checkpoints: primero adaptar un tokenizer manteniendo su
reconstrucción, medir deriva de códigos, recodificar corpus y readaptar el
generador. Reentrenar el tokenizer puede invalidar el generador publicado.
El entrenamiento conjunto posterior necesita resolver gradientes a través de
logits/códigos y sincronizar codebooks/cabezas; no está implementado aquí.

## Cómputo: lo medido y lo que falta

Se detectó RTX 3050 Laptop, 4096 MiB. El smoke test se ejecuta en CPU con dos
threads: el informe JSON registra duración de training y pico RSS del proceso
(incluye imports, construcción del dataset y ambos modelos), bajo tope de 4 GB.
No mide entrenamiento del tokenizer publicado ni generación NCM completa.

Para TinyStories, sólo los codebooks suman `12 × 4096 × 384 = 18,874,368`
elementos: 72 MiB en FP32, más aproximadamente otros 72 MiB para `ema_w`, sin
contar encoder, decoder, convoluciones, buffers, activaciones ni gradientes.
Como estimación contable, Adam en FP32 necesita alrededor de `16 × P` bytes para
P parámetros entrenables (pesos, gradientes, dos momentos); no incluye activaciones.
El cuantizador materializa distancias y one-hot por nivel: lote, longitud y
tamaño de codebook también importan. Una evaluación con GPT-2-large añade otro
modelo y no sirve para estimar directamente el coste de un tokenizer aislado.

No hay evidencia aquí para asegurar que un fine-tuning concreto cabe en 4/12 GB
ni para exigir un cluster para cualquier entrenamiento NCM. Hará falta medir
forward/backward de un checkpoint, batch mínimo, memoria pico y tokens/s; luego
estimar duración como tokens de entrenamiento divididos por throughput medido.
La razón de tokens reportada en el paper no se convierte directamente en ahorro
proporcional de GPU-horas para esta integración.

Se verificaron además 40 tests existentes de Matrix: estados, deducción, schemas,
reglas entre mundos, evaluador proposicional e importador OWL. Pasaron todos.

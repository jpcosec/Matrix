# Matrix × NCM: experimento contextual mínimo

El experimento de aprendizaje conjunto de [`SPEC.md`](SPEC.md) está implementado en
[`joint/`](joint/); diseño, decisiones y resultados en [`JOINT.md`](JOINT.md). El
código descrito abajo es el experimento mínimo anterior.

Código oficial clonado en [`ncm/`](ncm/), commit
`c70274273f489abc73832b2b98584a8483b6b203`.
El experimento usa su **VQ-VAE real**, con dimensiones pequeñas e inicialización
aleatoria. No descarga checkpoints ni entrena el generador NextConceptTransformer.

La hipótesis implementada es `z = f(texto, contexto)`: cambiar solamente el contexto
puede cambiar los códigos discretos y la evaluación de una misma proposición.
El contexto entra **antes de la cuantización**, mediante un embedding entrenable
y un adaptador. La cabeza de evaluación recibe únicamente la representación
cuantizada; no recibe el ID de contexto ni las etiquetas del oráculo por otro canal.

## Ejecutar

Desde esta carpeta, con el entorno `.venv` ya preparado:

```bash
bash ../matrix-shrdlu-spec/scripts/capped.sh 4 -- \
  env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python experiment.py --steps 250 --seed 7

bash ../matrix-shrdlu-spec/scripts/capped.sh 4 -- \
  env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider test_experiment.py
```

Para reconstruir el entorno en otra máquina:

```bash
uv venv .venv
uv pip install --python .venv/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python -r requirements-experiment.txt
```

La corrida usa CPU, dos threads y un tope de RAM de 4 GB. La GPU local detectada
es una RTX 3050 Laptop de 4 GB, pero no se utiliza. No se modificó el código upstream.

## Dataset y evaluación

[`dataset.py`](dataset.py) construye 560 consultas: 40 entidades, siete predicados y
dos contextos. Genera Turtle con un esquema explícito de aserciones, lo importa a
`Matrix/Matrix/src/operational_model` y obtiene sus etiquetas del motor.
Es un corpus sintético con textos controlados; **no implementa extracción RDF desde
prosa arbitraria**. Los textos fuente, hechos, negaciones y consultas se generan
desde la misma especificación. `EX.truth` y `EX.sense` son propiedades del esquema
del experimento, no semántica estándar inferida automáticamente de RDF.

| Consulta idéntica | Botánica | Fábula |
|---|---|---|
| El litre_000 es una planta. | verdadero | falso |
| El litre_000 es un animal. | falso | verdadero |
| El litre_000 hace fotosintesis. | verdadero, deducido | falso |
| El litre_000 puede caminar. | falso | verdadero, deducido |
| El litre_000 puede votar. | `unsinnig` | verdadero y aplicable |
| El litre_000 respira. | `sinnlos`, verdadero | `sinnlos`, verdadero |
| El litre_000 tiene flores. | desconocido | desconocido |

La fábula define explícitamente estos personajes como animales capaces de votar.
No estamos declarando universalmente que los árboles carezcan de sentido en
predicados políticos: la aplicabilidad es local al contexto de este fixture.

Las reglas son planta → fotosintético en botánica y animal → caminante en fábula.
Matrix las instancia y ejecuta `deduce()`. Una fila auxiliar impide que todas las
columnas verdaderas sean tautológicas; `respira` se mantiene deliberadamente
universal para comprobar que `sinnlos` no se castiga como `unsinnig`.

Se divide por entidad: 336 filas de entrenamiento, 112 de validación y 112 de test.
Ambos contextos de cada entidad permanecen en la misma partición. El vocabulario
se construye sólo con entrenamiento; nombres nuevos pasan a `<unk>`. Esta prueba
mide transferencia a otros identificadores dentro de reglas conocidas, no
generalización a contextos o relaciones nuevos. No se selecciona el mejor paso
usando test: se ejecutan 250 pasos fijos.

[`experiment.py`](experiment.py) entrena dos modelos con la misma semilla e igual
supervisión: con contexto y sin contexto. Agrega un baseline de mayoría por contexto,
sin texto. Evalúa verdad sólo cuando existe evidencia y la proposición es aplicable.
Evalúa aplicabilidad separadamente; las etiquetas desconocidas nunca se convierten
en falsas. Además evalúa las predicciones booleanas con `evaluate_formula()` del
kernel real de Matrix, y mide cambios de embedding y códigos al cambiar sólo Wi.

La pérdida es:

```text
L = CE_reconstrucción + L_VQ
    + 2 × (BCE_verdad_observada + BCE_aplicabilidad + 0.2 × L_implicación)

L_implicación(A → B) = -log(1 - p(A) × (1 - p(B)))
```

La última expresión usa dos Bernoulli independientes como aproximación declarada.
No convierte al kernel booleano en diferenciable. Las etiquetas y reglas de Matrix
supervisan una cabeza diferenciable, cuyo gradiente llega al encoder y al adaptador
mediante el straight-through del cuantizador upstream. Los codebooks conservan EMA.

## Artefactos

- [`artifacts/report.json`](artifacts/report.json): métricas, pérdidas, parámetros,
  tiempos, semilla, versión de torch, commit upstream y pico de RAM del proceso.
- [`artifacts/dataset/`](artifacts/dataset/): Turtle por contexto y JSONL por partición.
- [`artifacts/with_context_predictions.jsonl`](artifacts/with_context_predictions.jsonl)
  y su equivalente `without_context`: probabilidades y etiquetas por consulta.
- `artifacts/tiny_contextual_vqvae.pt`: pesos del experimento y vocabulario;
  no son pesos publicados por los autores de NCM.
- [`ANALISIS.md`](ANALISIS.md): auditoría de los puntos de integración y límites.

Los tests verifican separación de entidades, cambio de verdad con texto idéntico,
inferencia real de Matrix, exclusión de desconocidos, `sinnlos` versus `unsinnig`,
violaciones de implicación y propagación del gradiente hasta el encoder/contexto.

## Resultado observado (semilla 7, 250 pasos por modelo)

| Métrica de test | Sin contexto | Con contexto |
|---|---:|---:|
| Verdad, sólo conocidas y aplicables (88 filas) | 63,6% | 100% |
| Aplicabilidad (112 filas) | 92,9% | 100% |
| Ambos lados correctos en pares con verdad opuesta | 0% | 100% |
| Aceptación incorrecta de `unsinnig` | 100% | 0% |
| Violaciones booleanas de las reglas | 0% | 0% |
| Códigos que cambian al cambiar sólo contexto | 0% | 19,4% |

El baseline que usa sólo el contexto alcanza 63,6% en verdad. La reconstrucción
total alcanza 80,6% en ambos modelos; entre tokens del vocabulario de entrenamiento
es 100%. El 19,4% de tokens de entrada de test son nombres nuevos mapeados a `<unk>`;
el modelo no fue entrenado para reconstruir ese token. Se informa esa limitación
en lugar de presentar la reconstrucción como perfecta.

Cada modelo tiene 23.650 parámetros (22.114 entrenables). Cada entrenamiento duró
aproximadamente 1,5 segundos en CPU; el pico RSS de todo el proceso fue 519 MiB.
Estos tiempos excluyen instalación de dependencias y no estiman el coste de los
checkpoints publicados. Pasaron los cinco tests nuevos y 40 tests previos de Matrix.

Esta es una prueba del mecanismo. Un acierto alto en siete predicados sintéticos
no demuestra razonamiento abierto, una taxonomía emergente ni mejoras en generación.
El baseline sin contexto también puede satisfacer las reglas prediciendo valores
poco informativos: por eso se informa precisión y pares contextuales, no sólo
consistencia lógica. No se ha aislado aquí el beneficio causal de `L_implicación`
frente a las otras pérdidas supervisadas.

# Matrix × NCM: implementación del experimento conjunto (SPEC.md)

Implementación de [`SPEC.md`](SPEC.md) v0.1 en [`joint/`](joint/). Fecha: 29 de octubre de 2026.
Resultados: [`artifacts/joint/REPORT.md`](artifacts/joint/REPORT.md) y
[`artifacts/joint/report.json`](artifacts/joint/report.json); cada corrida en `artifacts/joint/runs/`.

## Ejecutar

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider joint/tests     # 33 tests de contrato
.venv/bin/python -m joint.evaluate --steps 3000                   # 5 variantes × semillas 7, 19, 41
.venv/bin/python -m joint.train --steps 3000 --seed 7             # una corrida + checkpoint
```

`--device auto` usa CUDA si está disponible. La tabla publicada se generó en una RTX 2060
(torch 2.14.1+cu130): ~2,7 min por corrida, 15 corridas en ~40 min, pico de ~1,5 GiB de VRAM.

**Autoridad Matrix.** El motor es la raíz de este repo. `MATRIX_ROOT` sólo hace falta para probar contra otro árbol.

## Módulos

| Archivo | Contenido |
|---|---|
| `joint/schema.py` | Registro del §2, validación (spans alineados, ≤64 tokens, sin truncar) y `model_inputs()`, único camino al encoder |
| `joint/fixture.py` | Dataset cruzado del §8, etiquetado por Matrix |
| `joint/matrix_adapter.py` | Oráculo de referencia inmutable, evaluador de fórmulas y exportación de rutas como `(routes_to wi_i wi_j)` |
| `joint/model.py` | Forward conjunto del §4 sobre el VQ-VAE real de NCM |
| `joint/asi_adapter.py` | Instantáneas, intensidad implicativa, propuestas y `L_ASI` |
| `joint/train.py` | Pérdidas del §7, trainer y checkpoints reanudables |
| `joint/evaluate.py` | Métricas del §9.2 y ablaciones |
| `joint/tests/` | Contratos del §9.1 y del fixture |

## Fixture (§8)

Tres dimensiones observables cruzadas: tema {finanzas, parque} × país {cl, es} × registro
{formal, coloquial}, es decir, ocho contextos de referencia. Cada uno compila a su propio
`LogicalSystem` con `WiGame.context_id` y un `Context` real (corrige la limitación del experimento
anterior). Se reservan para test, antes de entrenar, las combinaciones (parque, es, coloquial)
y (finanzas, cl, formal).

| Requisito §8 | Cómo se cumple |
|---|---|
| 1. mismo signo, referentes distintos | `banco` (tema), `guagua` y `micro` (país), `pega` (país × registro) |
| 2. signos distintos, un referente | `palta`/`aguacate` siempre; `guagua`/`autobús` sólo en es; `micro`/`autobús` sólo en cl |
| 3. ≥3 dimensiones, combinaciones reservadas | ver arriba; métricas separadas por combinación vista/no vista |
| 4. verdadero, falso, desconocido, inaplicable | vía `get_status`; además consultas fuera de ejes, sin etiqueta de sentido |
| 5. dos organizaciones alternativas | p. ej. `banco tiene_respaldo`: costo definido por tema, desconocido por país; `guagua elector`: al revés |
| 6. rasgo universal frente a discriminante | `existe` es `sinnlos` (no discrimina); las demás clases sí |
| 7. soporte ASI | 3000 registros de train; la primera instantánea ya tiene propuestas elegibles |

Splits por grupo fuente, con todas las variantes contextuales de un fragmento en la misma partición:
train 500 grupos × 6 contextos vistos (3000), validación 360, entidades nuevas 360 (nombres
fuera del vocabulario) y combinaciones de test 640 (480 vistas, 160 no vistas). El contexto
observable falta en ~25% de las dimensiones; el texto lleva pistas léxicas (`cachai`, `po`,
`en la plaza`...) que a veces compensan esa ausencia y a veces no.

## Decisiones de interpretación

Puntos que el SPEC deja abiertos y cómo se resolvieron:

- **Encoder.** Es el `Encoder` de NCM con `enc_layers=2` (atención bidireccional). Con `enc_layers=0`
  no habría mezcla entre tokens y una mención no podría ver las pistas del resto del fragmento.
  El contexto observable se suma después del encoder.
- **Minibatch.** Son 8 fragmentos fuente con todas sus variantes contrafácticas (~48 registros),
  para que los pares contrafácticos entren juntos.
- **`m0`.** Usa el contexto observable en lugar de `u`, que todavía no existe en ese paso.
- **Descriptor de la consulta.** Se usa `u` de la mención sujeto.
- **Perfiles `C`.** Son las 27 conjunciones parciales del esquema, todas con valores presentes en train.
  `E[c]` es una proyección aprendida de la media de embeddings de los atributos del perfil
  (compartidos con el contexto observable).
- **Costo de ruta.** Se normaliza por la masa sobre perfiles con costo conocido, así poner masa en
  perfiles desconocidos no reduce la pérdida. La masa desconocida se reporta aparte (`unknown_cost_mass`).
- **Lógica.** Se usan fórmulas de dos átomos (`persona → ser_vivo`, `vehiculo → objeto` y dos
  exclusiones), sólo cuando la referencia verifica que ambos átomos son aplicables. Las
  asignaciones que falsifican cada fórmula las enumera `evaluate_formula` de Matrix.
- **ASI.** El único puente a autograd es el ranking de rutas *atributo observado → Wi* (§6), con el
  contexto de ruta medio del batch. Las propuestas `projection`, `gate` y `discriminant` se calculan,
  se versionan y se guardan, pero no entran en ninguna pérdida. La intensidad es la clásica de Gras
  con cola de Poisson exacta y conteos int64, implementada aquí; no se importó `sia/` ni `pipeline/`
  de `matrix-shrdlu-spec`.
- **Efectos laterales de la instantánea.** El cuantizador NCM no aplica EMA en eval, pero sí marca
  `codebook_hit_*`; la instantánea restaura esos contadores, así que no deja ningún efecto lateral.
- **Ruteo congelado.** Se congela una copia del scorer usada sólo para rutas, junto con `U`, `A`, el
  endpoint de entrada, el contexto de ruta y sus proyecciones de rol. El scorer de proposiciones
  sigue entrenando.
- **Adaptador Matrix.** Lee celdas con `get_status` (sin bitmasks, sin ensamblar bloques, sin
  `assert`). Las máscaras `unsinnig` se aplican después de los hechos y de `deduce()`, porque
  `add_fact` escribe `sinnvoll` y las pisaría; el adaptador verifica que ninguna se pierda.

## Pruebas de aceptación (§9.1)

Los 33 tests pasan (`joint/tests`, ~15 s en CPU). Cubren:
- gradientes finitos y no nulos en encoder, `F`, `U`, `A`, scorer y contexto de ruta, y que la
  pérdida de verdad sola llega al ruteo;
- gradiente a través de ambos pasos de refinamiento;
- que cambiar una ruta altera `H`, `m`, la correspondencia y las consultas;
- que las rutas ejecutadas coinciden con las proposiciones `routes_to` exportadas;
- que el oráculo distingue desconocido, falso, `unsinnig` y `sinnlos` sin mutar la referencia
  (huella SHA-256 de todas las celdas);
- que marcar todo inaplicable no elimina ninguna obligación;
- que dos instantáneas ASI se reconstruyen desde las asignaciones vigentes;
- que permutar slots conjuntamente deja las salidas invariantes;
- que un checkpoint reanuda el paso siguiente con la misma pérdida;
- los contratos de esquema, del fixture y los valores de referencia de la intensidad.

El test de "cambiar una ruta" verifica el cableado con descriptores separados a mano, porque
con pocos pasos los Wi aún no se diferencian. El efecto en un modelo entrenado se midió aparte:
con 1500 pasos, forzar otro Wi mueve `H` hasta 2,0 y `m` hasta 0,30, y cambia el 15% de las
predicciones de verdad.

## Resultados (§9.2)

3000 pasos, semillas 7, 19 y 41, media ± desviación estándar muestral.
Combinaciones de contexto **no vistas** (160 registros, ~2450 consultas puntuadas):

| Métrica | completo | sin ASI | ruteo congelado | sin contexto | sin lógica |
|---|---:|---:|---:|---:|---:|
| Verdad (conocida y aplicable) | 0,981 ± 0,005 | 0,983 ± 0,001 | 0,930 ± 0,003 | 0,936 ± 0,001 | 0,982 ± 0,004 |
| Aplicabilidad | 0,998 | 0,998 | 0,985 | 0,988 | 0,998 |
| Aceptación falsa de `unsinnig` | 0,009 | 0,006 | 0,055 | 0,043 | 0,006 |
| Correspondencia | 0,989 | 0,991 | 0,989 | 0,962 | 0,989 |
| Cobertura | 0,999 | 0,999 | 0,990 | 0,992 | 0,999 |
| Violaciones lógicas discretas | 0,000 | 0,000 | 0,000 | 0,000 | 0,000 |
| Costo de ruta | 0,115 | 0,115 | 0,115 | 0,115 | 0,115 |
| Wi usados | 15,3 ± 7,5 | 16,7 ± 1,5 | 2,0 ± 1,0 | 13,3 ± 4,7 | 8,3 ± 1,2 |

Las demás particiones están en `REPORT.md`. En combinaciones vistas, el modelo completo llega a
0,994 de verdad; en entidades nuevas, a 0,991 ± 0,002, contra 0,972 ± 0,027 sin ASI y
0,959 ± 0,058 sin lógica, diferencias que caben dentro de la variación entre semillas.

### Lectura

Con el criterio del SPEC ("mejora bajo contextos reservados y supera las ablaciones relevantes
sin perder cobertura"):

- **Ruteo aprendido y contexto: sí aportan.** En combinaciones no vistas, el modelo completo supera
  al ruteo congelado y al modelo sin contexto en ~5 puntos de verdad. También reduce la aceptación
  de `unsinnig` de ~5% a <1%, sin perder cobertura, de forma consistente en las tres semillas.
- **ASI: sin efecto medible.** "Sin ASI" iguala al completo en combinaciones no vistas. La ventaja
  en entidades nuevas no es significativa con tres semillas.
- **Pérdida lógica: sin efecto medible.** Las violaciones discretas son 0 también sin ella: en este
  fixture las reglas ya están implícitas en la supervisión de verdad.
- **Costo de ruta: inerte.** Da el mismo valor en todas las variantes. `softmax(A)` queda casi
  uniforme (entropía 3,276 de un máximo de 3,296), así que el mapeo Wi → perfiles no se aprende.
  Una sonda con peso 1,0 en vez de 0,01 (semilla 7,
  `artifacts/joint/probe_route_cost_weight1_seed7.json`) sólo lo baja de 0,126 a 0,121.
  Hipótesis no verificada: como el conjunto de consultas incluye a propósito cruces inaplicables,
  bajo el perfil correcto esos cuestan 1, y la tabla casi no discrimina entre perfiles. Hay que
  revisar el diseño del término o del fixture antes de interpretar §3.1 (`A`) como aprendido.
- La ocupación de campos es baja (5–7 de 64, con mezclas suaves de entropía ~1,1). La correspondencia
  se resuelve igual, pero no hay que leer los slots como conceptos.

Esto es una prueba del mecanismo sobre un fixture sintético controlado. No demuestra
razonamiento abierto, taxonomía emergente ni capacidad de generación (§10).

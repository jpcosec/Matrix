# `experiments/` — prueba sobre corpus grandes

Ejecuta el pipeline completo (Populator → SIA → Matrix) sobre un corpus, escribe los
artefactos del mundo, verifica que la información se recupera con procedencia y
comprueba que el `WiGame` sobrevive a un viaje por YAML.

## Cómo ejecutar

```bash
python -m experiments.run_corpus <dir|archivo> --wigame <id> [opciones]
```

Opciones principales:
- `--lang es|en` — lista de stopwords del populator.
- `--max-concepts N` — tope de conceptos (los de mayor frecuencia de documento). Por defecto 800.
- `--max-facts N` — tope de candidatos `fact` (top-K por φ entrópica). Por defecto 3000.
- `--max-nonsense N` — tope de candidatos `nonsense` (top-K por `n_a·n_b`). Por defecto 500.
- `--max-classes N` — tope de candidatos `class`. Por defecto 15.
- `--hierarchy-concepts N` — si se indica, la jerarquía se calcula sobre los N conceptos más
  frecuentes. Por defecto `None` (sin submuestreo): `significant_levels` está vectorizado y
  corre en < 1 s con 800 conceptos.
- `--min-confirmed N` — si hay menos hechos confirmados, se promueven las reglas de mayor φ
  de la cola para poder medir recuperación. Por defecto 30.
- `--recursive` — lee directorios recursivamente.
- `--out <dir>` — destino de los artefactos.

Ejemplos:

```bash
python -m experiments.run_corpus corpus/vegetales --wigame vegetales --lang es --out /tmp/corpora/vegetales
python -m experiments.run_corpus /home/jp/proyectos/Matrix/TractatusKnowledgeMachine/atoms \
    --wigame atoms --lang es --recursive --out /tmp/corpora/atoms
python -m experiments.run_corpus /tmp/corpora/sia_book.txt --wigame siabook --lang en --out /tmp/corpora/siabook
```

## Qué mide

- **Escritura:** nº de documentos/oraciones/conceptos, S-expressions evaluadas, candidatos por
  tipo, auto-confirmados, hechos en `V_i` y derivados, tiempos por etapa y memoria pico.
- **Recuperación con procedencia (`retrieval.md`):** para los 30 hechos confirmados de mayor φ
  ejecuta `(why wigame:<id> (implies a b))` y comprueba que **cada** `prov` apunta a un span del
  documento original cuyo texto contiene la secuencia de tokens de `a` y de `b`. Objetivo ≥ 95 %.
- **Consultas de retorno (`queries.md`):** `(return facts symbol:<c> …)` para los 10 conceptos más
  frecuentes y `(check …)` sobre 5 reglas confirmadas y 5 pares nonsense.
- **Persistencia:** `world.yaml` (más `system_extras.yaml` con reglas y cola de candidatos), y
  comparación de 5 `check` y 3 `why` antes/después de recargar: deben ser idénticos.

## Artefactos

`stats.json`, `rules_top.md` (40 reglas por φ + 15 clases significativas), `retrieval.md`,
`queries.md`, `persistence.md`, `world.yaml`, `system_extras.yaml`.

## Notas

- Los corpus grandes **no** se versionan: los PDFs se convierten con `pdftotext` y las rutas
  externas son de solo lectura.
- Los topes (`--max-*`) son los del CLI del experimento; `pipeline.build_system` mantiene
  `None` por defecto para no cambiar el comportamiento del pipeline pequeño.

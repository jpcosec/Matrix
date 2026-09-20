# Matrix Engine

Matrix stands for **Minimal Agglomerative Text Retrieval Index**.

It is a logic-oriented knowledge engine for projecting natural-language statements into structured contexts, evaluating whether relational propositions are meaningful inside those contexts, and operating on the resulting matrices.

The project centers on **sense/meaning matrices**: a separation between truth (`V_i`) and applicability (`S_i`) inside logical worlds (`W_i`). On top of that representation, the engine supports search, ambiguity detection, tautology detection, context composition, bridge routing, and proposition-first ingestion workflows.

## What is in this repository

- `src/operational_model/` — runtime proposition-first: `Thing`, `Relation`, `Proposition`, `Fact`, `WiGame`, `Context`, `RoutingProjection`, matrices y sistema.
- `src/operational_model/kernel/` — capa de fórmulas, booleana, bitwise y aserciones tipadas.
- `tools/kb/` — harness de KB: convierte texto, código o specs en `WiGame`s context-scoped con revisión y verificación. Ver [`tools/kb/README.md`](tools/kb/README.md).
- `examples/` — demos ejecutables, specs y KBs versionadas consultables offline. Ver [`examples/README.md`](examples/README.md).
- `desk/drawer/shrdlu/` — prototipo separado que baja inglés controlado a operaciones del runtime.
- `tests/` — suite completa (`pytest`, 133 tests).
- `docs/README.md` — índice de arquitectura y conceptos.

## Quick start

```bash
pip install -e .
pytest

# prototipo SHRDLU (inglés controlado)
python desk/drawer/shrdlu/proto.py --once "Put the red block on the blue cube."

# KB: de texto a WiGames consultables
python -m tools.kb --kb kb machine                       # operatoria + FSM/recetas (sin LLM)
python -m tools.kb --kb kb ingest
python -m tools.kb --kb kb review all --decision approved --reviewer me
python -m tools.kb --kb kb compile
python -m tools.kb --kb kb reachability
python -m tools.kb --kb kb query "(check wigame:ragout:precede (precede picar servir))"
```

## Core ideas

- `W_i`: a logical context with its own admissible terms, relations, metadata, and facts.
- `(R a b)`: la forma relacional canónica del modelo activo.
- `V_i`: la matriz de verdad para una relación context-relative sobre `axis_a × axis_b`.
- `S_i`: la máscara de sentido/aplicabilidad del mismo espacio relacional.
- `kern:{symbol}`: namespace del kernel para átomos no relacionales en fórmulas proposicionales.
- `SearchVector`: vector de consulta local dentro de un `WiGame`.
- `RoutingProjection`: proyección de sujetos entre `WiGame`s; no vacía sólo si comparten referente canónico.
- `Hipertensor` / `WiGame`: la dirección canónica es un almacén global de hechos del que los `WiGame` son proyecciones locales.
- provenance: fuente, confianza o derivación guardadas en el `Fact`.
- `D_i`: máscara discriminativa que identifica dimensiones no informativas.
- `sinnvoll` / `sinnlos` / `unsinnig`: proposición significativa, estructura tautológica/contradictoria, o fuera del espacio lógico.

## Contexto y desambiguación

Un `WiGame` **no** es un par de ejes bajo una relación: es ese par **bajo un contexto**. El contexto es parte de la identidad (`context_id`), `Si` es local, y los contextos forman un árbol. Acumular contextos estrecha el referente de un símbolo en vez de multiplicar homónimos; la identidad entre contextos se decide por curación (`aliases`) y se materializa como `RoutingProjection`.

- [`docs/context_and_wigame.md`](docs/context_and_wigame.md)
- [`docs/operatoria_recetas.md`](docs/operatoria_recetas.md) — contenido secuencial (instrucciones) como máquina de estados.

## Contenido secuencial

Para instrucciones y procedimientos hace falta una **operatoria de dominio** autorada (relaciones, álgebra, operaciones admisibles, errores tipificados). Con eso, `Vi[estado][estado]` es la matriz de transición, `Si` es la guarda, el cierre transitivo da alcanzabilidad y las firmas de salida dan minimización de estados.

```bash
python -m tools.kb --kb kb reachability     # cierre vs oráculo BFS, ciclos, inalcanzables, equivalencias
python -m tools.kb --kb kb shared --symbol cebolla
```

## Runtime surface

The active direct surface is s-expression-first.

```text
(create symbol dog perro)
(create relation es es)
(create li li:animales es (axis-a dog) (axis-b mammal))
(create wigame wigame:animales li:animales)
(ingest wigame:animales (es dog mammal))
(assert wigame:animales (es dog mammal))
(check wigame:animales (es dog mammal))
```

## Schema

- `schemas/schema.yaml` — forma serializada de un `WiGame` (Li/Vi/Si/facts).
- `docs/canonical_forms_and_ingestion.md` — forma canónica externa `(R a b)`.

## Running tests

```bash
pytest                 # suite completa
pytest -q tests/test_kb_machine.py tests/test_kb_fanout.py
```

## Documentation map

- `docs/README.md` — índice de docs
- `docs/proposition_first_architecture.md` — dirección arquitectónica estable
- `docs/context_and_wigame.md` — WiGame bajo contexto, árbol de contextos y desambiguación
- `docs/operatoria_recetas.md` — operatoria de dominio: cómo leer una receta como máquina de estados
- `docs/kb_fanout_harness.md` — harness de KB: pipeline, mediciones, stress y capacidades
- `docs/canonical_forms_and_ingestion.md` — forma canónica y reglas de ingesta
- `docs/kernel_symbol_policy.md` — kernel vs Wi, capas de ejecución y política de átomos
- `docs/rebuild_and_migration_policy.md` — política de migración
- `docs/architecture.md` — layout de paquetes y responsabilidades
- `docs/concepts.md` — vocabulario filosófico y proposition-first
- `docs/data_models.md` — estructuras primarias
- `docs/operations.md` — ingesta, evaluación, ruteo y reconstrucción
- `docs/storage_boundary.md` — YAML-first y compatibilidad Postgres
- `tools/kb/README.md` — manual del harness (CLI, layout, gates, extensión)
- `examples/README.md` — catálogo de ejemplos, demos y KBs versionadas

## License

Apache 2.0

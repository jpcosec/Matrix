# Matrix-SHRDLU

Motor de conocimiento que **puebla** mundos lógicos desde texto crudo (chunker estadístico → CHIC/SIA → candidatos con cita de origen → curado) y que se **usa** conversando como con SHRDLU. Especificación en [`specs/`](specs/README.md).

```
corpus/*.md ─► populator/ ─► sia/ ─► pipeline/bridge ─► matrix/ runtime (candidatos, promote, deduce) ─► REPL
```

| Paquete | Qué hace |
|---|---|
| `populator/` | oraciones con offsets → tokens → frases multi-palabra → `Corpus` (`X` binaria individuos × conceptos) |
| `sia/` | intensidad de implicación clásica y entrópica, cohesión, jerarquía implicativa, grafo (Gras/Couturier, SCI 127) |
| `pipeline/` | `sia` → S-expressions `create`/`candidate` con `Prov(f)`; `build_system` alimenta el runtime y auto-confirma reglas fuertes |
| `matrix/` | motor booleano (subtree de `jpcosec/Matrix`): `WiGame`, `S_i`/`V_i`, `I`, runtime S-expr con `candidate / promote / reject / retract / why / define` |
| `matrix/prototypes/shrdlu/` | REPL en español controlado con aclaración por ambigüedad y elipsis |
| `corpus/vegetales/` | corpus de prueba (295 oraciones) |

## Uso

```bash
# tests (55 en la raíz: sia, populator, bridge, e2e · 162 en matrix/)
python -m pytest -q tests/
( cd matrix && python -m pytest -q )

# poblar un mundo desde el corpus
python -m pipeline.run corpus/vegetales --wigame vegetales --dump /tmp/vegetales.yaml

# conversar
cd matrix && PYTHONPATH=.. python -m prototypes.shrdlu.repl ../corpus/vegetales

# proyecciones entre dos mundos (AROMA) y curado asistido por LLM
python -m pipeline.match corpus/a corpus/b --wigames a b --phi-r 0.85
python -m pipeline.curate corpus/vegetales --wigame vegetales --backend pi --limit 10

# escribir y recuperar sobre un corpus grande (docs, libro, trazas)
python -m experiments.run_corpus <dir|archivo> --wigame <id> --lang es|en --recursive --out /tmp/corpora/<id>
```

`experiments/run_corpus.py` puebla un mundo, comprueba que cada `prov` de los 30 hechos más fuertes cita una oración que contiene ambos conceptos, ejecuta consultas y recarga el mundo desde YAML. Resultados sobre 273 documentos de proyecto (3.9k oraciones), un libro (17k oraciones) y trazas de agentes: recuperación con procedencia 100 %, recarga idéntica, 0.03-23 s, < 300 MB.

```
> ¿la lechuga tiene hoja?
Sí.
> ¿y raíz?
No lo sé (nadie lo ha confirmado).
> ¿por qué la lechuga tiene hoja?
porque (implies lechuga hoja) [confirmed; corpus/vegetales/01_lechugas.md:0-48, …]
> la espinaca tiene tallo
Hecho.
> candidatos          # cola de curado: aprueba <id> · rechaza <id> <motivo>
```

Dependencias: Python ≥ 3.10, `numpy`, `scipy`, `pyyaml`. Los PDF de referencia no se versionan (ver `specs/sources.md`).

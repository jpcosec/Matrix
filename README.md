# Matrix-SHRDLU

Motor de conocimiento que **puebla** mundos lógicos (`WiGame`) desde texto crudo y que se **usa**
conversando como con SHRDLU. El puente texto → Matrix es la **convergencia**: cada chunk es un
contexto de uso con sus signos locales, la identidad entre contextos se propone por convergencia de
símbolos y se confirma por regla o curado. Especificación en [`specs/`](specs/README.md); el diseño
que prevalece está en [`specs/convergence.md`](specs/convergence.md).

```
texto ─► populator: chunks (contextos), signos locales, offsets
              │
              ▼
      descompositor por oración (heurística o LLM) ─► declaraciones (R a b) @contexto, con Prov
              │
              ▼
      pipeline.ingest: un WiGame por (contexto, relación) con hechos `observed`
              │
              ▼
      pipeline.convergence (CHIC/SIA): árbol de contextos · proyecciones / equivalent · compuertas, D_i
              │
              ▼
      promoción por convergencia o curado ─► consultas ruteadas (ask) con ruta y cita
```

| Paquete | Qué hace |
|---|---|
| `populator/` | documentos → chunks (contextos) → signos locales con offsets (`read_documents`, `build_contexts`) |
| `sia/` | intensidad implicativa (ϕ, φ entrópica), cohesión, jerarquía, niveles significativos, similitud, AROMA |
| `pipeline/` | descomposición por oración, ingesta por contexto, convergencia por pares candidatos y lotes, consultas ruteadas, curado |
| `matrix/` | motor booleano (subtree de `jpcosec/Matrix`): `WiGame`, `S_i`/`V_i`, `I`, runtime S-expr (`check / assert / ingest / create / promote / why / …`) |
| `matrix/prototypes/shrdlu/` | REPL en español e inglés controlado sobre el mundo construido |
| `corpus/physicists/` | corpus de evaluación (89 físicos: Simple English + EN + Wikidata + GAP) |

> **Documentación técnica:** [`docs/technical.md`](docs/technical.md). Módulos, estructuras de datos, parámetros, comandos, corpus, métricas, resultados medidos y limitaciones.

## Uso

Toda evaluación va **bajo tope de memoria** (`bash scripts/capped.sh 4 -- …`, ver
[`experiments/README.md`](experiments/README.md)) y una corrida por comando.

```bash
# tests (131 en la raíz: populator, descomposición, ingesta, convergencia, consultas · 179 en matrix/)
python -m pytest -q tests/
( cd matrix && python -m pytest -q )

# ingesta por contexto: chunks → WiGames + convergencia
python -m pipeline.ingest corpus/physicists --lang en --unit document
# taxonomía de contextos, convergencia de símbolos y mantenimiento de W_i
python -m pipeline.convergence corpus/physicists --lang en --unit document

# descompositor LLM por chunk (una vez; la caché queda en corpus/physicists/declarations_llm.jsonl)
bash scripts/capped.sh 4 -- python -m pipeline.decompose_batch corpus/physicists --regime pairs --backend pi

# evaluación, un comando por descompositor
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer heuristic
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer llm
bash scripts/capped.sh 4 -- python -m experiments.eval_physicists --regime pairs --decomposer both

# poblar un mundo y conversar
python -m pipeline.run corpus/physicists --wigame physicists --dump /tmp/physicists
( cd matrix && PYTHONPATH=.. python -m prototypes.shrdlu.repl ../corpus/physicists/articles --lang en --limit 20 )

# curado asistido por LLM (el backend propone; el humano confirma)
python -m pipeline.curate corpus/physicists --backend pi --limit 10
```

```
> was Curie born in Warsaw?
Sí: (born_in curie@Q7186 warsaw@Q7186) [corpus/physicists/en/Q7186.md:938-962] · ruta: wigame:Q7186:born_in
> why?
porque (born_in curie@Q7186 warsaw@Q7186) [observed; corpus/physicists/en/Q7186.md:938-962]
> ¿por qué la lechuga tiene hoja_lisa?
porque (has_property lechuga@01_lechugas hoja_lisa@01_lechugas) [observed; corpus/vegetales/01_lechugas.md:14-38]
> candidatos          # cola de curado: aprueba <id> · rechaza <id> <motivo> · sugiere <id>
```

Dependencias: Python ≥ 3.10, `numpy`, `scipy`, `pyyaml`. Los PDF de referencia no se versionan (ver
[`specs/sources.md`](specs/sources.md)).

## Resultados

Corpus `corpus/physicists`, régimen `pairs` (178 contextos = 89 artículos Simple + 89 lead EN: los
dos contextos por físico). Detalle completo en [`.herdr/llm_report.md`](.herdr/llm_report.md) y
[`specs/convergence.md`](specs/convergence.md) §7.

| métrica | heuristic | llm | both |
|---|---|---|---|
| declaraciones | 2 931 | 11 242 | 13 574 |
| símbolos / variables (≥ 2 declaraciones) | 4 120 / 690 | 10 703 / 4 427 | 12 277 / 5 701 |
| pares candidatos (≥ 1 configuración compartida) | 37 | 275 | 326 |
| convergencia entre fuentes (personas) | 1/77 = 0.013 | 5/79 = 0.063 | 8/81 = 0.099 |
| intra-contexto | 0/157 | 0/158 | 0/161 |
| ranking MRR / hit@1 / hit@3 (todas las consultas) | 0.055 / 0.043 / 0.053 | 0.265 / 0.250 / 0.261 | 0.243 / 0.219 / 0.250 |
| consultas rankeadas / unranked | 13 / 81 | 34 / 58 | 38 / 58 |
| falsas fusiones | 0 | 0 | 1 |
| QA Wikidata (recall etiqueta / con salto) | 0.002 / 0.0 | 0.011 / 0.048 | 0.012 / 0.045 |
| basura (plantada vs real aislada) | 1.0 vs 0.98 | 1.0 vs 0.96 | 1.0 vs 0.92 |
| promovidos / propuestos / referentes | 6 / 65 / 3 | 45 / 296 / 18 | 98 / 352 / 42 |
| memoria pico / tiempo | 198 MB / 2.5 s | 250 MB / 10.2 s | 274 MB / 14.4 s |

Otros regímenes (descompositor `heuristic`, re-ejecutados con la misma regla de convergencia):

| régimen | contextos / símbolos | promovidos / propuestos | QA etiqueta | basura (plantada vs real) |
|---|---|---|---|---|
| `document` Simple | 89 / 2 719 | 0 / 11 | 0.002 | 1.0 vs 0.94 |
| `document` EN | 89 / 15 545 | 4 / 21 | 0.007 | 1.0 vs 0.92 |
| `section` EN | 564 / 17 691 | 3 / 61 | 0.0 | 1.0 vs 1.0 |
| `pairs` | 178 / 4 120 | 6 / 65 | 0.002 | 1.0 vs 0.98 |

## Qué aprendimos

- **El algoritmo converge en el régimen multi-fuente cuando hay ≥ 2 configuraciones informativas
  compartidas.** Con dos contextos por físico (Simple + lead EN) la guarda de promoción casi nunca
  se alcanza: convergen 1/77 personas con la heurística y 5/79 con el LLM. La intra-contexto
  (pronombre y etiqueta del mismo artículo) es 0 en los tres modos: comparten a lo sumo una
  configuración.
- **El cuello de botella en texto real es la capa de declaraciones, no la promoción.** Los mismos
  hechos se lexicalizan distinto en cada fuente (`Nobel Prize` vs `Nobel Prize in Chemistry`),
  así que la solución no está en bajar el umbral sino en canonicalizar objetos vía `equivalent`.
- **El LLM como descompositor de superficie sube la señal sin fusiones falsas:** triplica las
  declaraciones, multiplica por cinco la convergencia entre fuentes (0.013 → 0.063) y por ~50 el QA
  con salto (0.0 → 0.048), y sube el MRR de 0.055 a 0.265. El modo `both` gana cobertura
  (8/81) al precio de una falsa fusión.
- **La basura queda aislada siempre:** el 100 % de los 50 hechos plantados no encuentra
  configuraciones compatibles, frente al 96 % de los hechos reales.
- **Nunca `p×p`:** tres corridas sin tope murieron por OOM el 2026-09-20. La intensidad se calcula
  sobre la lista de **pares candidatos** (índice invertido configuración → símbolos) y la
  convergencia entra por **lotes**; el pico del régimen `document` EN bajó de 7.9 GB a 250 MB.
  Por eso toda evaluación va con `bash scripts/capped.sh 4 -- …`.

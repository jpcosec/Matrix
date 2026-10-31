# Examples (gold catalog)

Everything reproducible that we extracted while building the KB harness. Raw KBs
are build outputs (usually in `/tmp`); what is committed here are **specs,
scripts, reports and digests**.

## Executable demos

| example | qué es | comando | resultado |
|---|---|---|---|
| `ragout_demonstration.py` | demo culinario de 5 etapas: ingesta atómica → W_base → D_i → filtro `Si` → `W* = (Vi ∨ Di) ∧ Si` | `python examples/ragout_demonstration.py` | `ragout_champinones` sin alucinar `ragout_carne` (test: `tests/test_ragout_demonstration.py`) |
| `collect_digests.py` | resume cualquier KB en un digest commiteable | `python examples/collect_digests.py /tmp/kbmach=machine_recipes` | `examples/reports/*.digest.json` |
| `regenerate.sh` | reconstruye la parte determinística (máquinas + tests + digests) | `bash examples/regenerate.sh` | KB de máquinas + suite verde |

## Specs (autoradas, son la fuente)

| specs | dominio | contenido |
|---|---|---|
| `tools/kb/operatoria/recetas.yaml` | recetas | `precede` transitivo, `sustituye_a` transitivo, `paralelo_con` conmutativo, operaciones (`cierre`, `aciclico`, `alcanzable`, `guarda`) y errores tipificados |
| `tools/kb/operatoria/fsm.yaml` | fsm | `precede` transitivo; operaciones `alcanzable`, `scc`, `minimizar_estados`; ciclos permitidos |
| `tools/kb/machines/trafico.yaml` | fsm | semáforo con estado inalcanzable y estado equivalente |
| `tools/kb/machines/ascensor.yaml` | fsm | FSM fuertemente conectada de 3 pisos |
| `tools/kb/machines/ragout.yaml` | recetas | receta lineal acíclica con precondiciones e ingredientes |
| `tools/kb/machines/bechamel.yaml` | recetas | receta con cadena de sustitución transitiva |
| `tools/kb/machines/guiso.yaml` | recetas | receta que comparte ingredientes con el ragout |

## Digests commiteados

| ejemplo | facts | contextos | wigames | proyecciones | derivados | notas |
|---|---|---|---|---|---|---|
| `machine_recipes` | 103 | 6 | 20 | 8 | 34 (cierre) | recetas acíclicas, FSM con ciclo, `verde_peatonal` inalcanzable y equivalente a `verde` |
| `software_matrix` | 1494 | 86 | 211 | 1736 | — | AST de este repo; homónimos de código (`post_init` en 4 clases) |
| `wikipedia_10_articles` | 693 | 10 | 102 | 50 | — | Curies, Meitner, Hahn, Franklin, Watson, Crick, Einstein, Bohr; `nuclear_fission` compartido Bohr↔Hahn |
| `wikipedia_marie_curie` | 71 | 1 | 4 | 0 | — | un artículo, curación de `she/curie/maria` → `marie_curie` |

## KBs versionadas (queryables offline)

La extracción con LLM no es regenerable barato, así que se versiona lo no derivable (`proposals/`, `review.yaml`, `aliases.yaml`, `relations.yaml`, `sources/*.json`) y se deja derivable el resto (`compile` reconstruye `facts/`, `wigames/`, `contexts.yaml`, `projections/`, `shared.yaml`).

| KB | qué tiene | cómo se usa |
|---|---|---|
| `kb_wikipedia_10_articles/` | 10 artículos, 693 facts materializados, 50 proyecciones, curación de pronombres y apellidos | `python -m tools.kb --kb examples/kb_wikipedia_10_articles compile && python -m tools.kb --kb examples/kb_wikipedia_10_articles verify --fail-on-problems` |
| `kb_wikipedia_marie_curie/` | un artículo, 71 facts, 4 WiGames, alias `she/curie/maria` | idem con `examples/kb_wikipedia_marie_curie` |

Ejemplos verificados de consulta:

```bash
python -m tools.kb --kb examples/kb_wikipedia_10_articles query \
    "(check wigame:niels_bohr:descubierto_por (descubierto_por nuclear_fission otto_hahn))"
python -m tools.kb --kb examples/kb_wikipedia_10_articles shared --symbol polonium   # irene <-> marie <-> pierre
python -m tools.kb --kb examples/kb_wikipedia_marie_curie query \
    "(check wigame:marie_curie:nace_en (nace_en marie_curie warsaw))"
```

Cada carpeta trae su propio `README.md` con el detalle y el resultado esperado.

## Cómo regenerar

Determinístico (sin LLM, sin red salvo tests):

```bash
bash examples/regenerate.sh
```

Corpus de texto (requiere workers free `pi` + `deepseek-flash`):

```bash
python -m tools.kb --kb kb fetch "Marie Curie"
python -m tools.kb --kb kb prepare --max-chars 2500
bash examples/fanout.sh kb 6                # 1 worker por chunk
python -m tools.kb --kb kb ingest
python -m tools.kb --kb kb review all --decision approved --reviewer jp
python -m tools.kb --kb kb aliases \
    --add 'marie_curie:she=marie_curie' --add 'marie_curie:curie=marie_curie'
python -m tools.kb --kb kb compile
python -m tools.kb --kb kb verify --fail-on-problems
python examples/collect_digests.py kb=mi_ejemplo
```

Corpus de software (AST, sin LLM):

```bash
python -m tools.kb --kb kb software --path src/operational_model --path tests --base .
python -m tools.kb --kb kb ingest && python -m tools.kb --kb kb review all --decision approved --reviewer ast
python -m tools.kb --kb kb compile && python -m tools.kb --kb kb verify --fail-on-problems
```

Máquinas y recetas (specs autoradas):

```bash
python -m tools.kb --kb kb machine
python -m tools.kb --kb kb ingest && python -m tools.kb --kb kb review all --decision approved --reviewer operatoria
python -m tools.kb --kb kb compile
python -m tools.kb --kb kb reachability        # cierre vs oráculo BFS, ciclos, inalcanzables, equivalencias
python -m tools.kb --kb kb shared --symbol cebolla
```

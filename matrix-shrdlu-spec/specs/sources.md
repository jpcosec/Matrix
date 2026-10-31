# Fuentes

Los PDF no se versionan (`.gitignore`); se citan por ruta local y página impresa.

## Algoritmo (CHIC / SIA)
- **Gras, Suzuki, Guillet, Spagnolo (eds.).** *Statistical Implicative Analysis: Theory and Applications.* Studies in Computational Intelligence 127, Springer, 2008. e-ISBN 978-3-540-78983-3. Local: `978-3-540-78983-3.pdf` (raíz; página PDF = impresa + 13).
  - Cap. 1, Gras & Kuntz, *An overview of the SIA development*, pp. 11-40: índice `q`, intensidad `ϕ`, versión entrópica, R-reglas, cohesión, jerarquía implicativa, niveles significativos, tipicidad/contribución.
  - Cap. 2, Couturier, *CHIC: Cohesive Hierarchical Implicative Classification*, pp. 41-53: tipos de variable, árbol de similitud, jerarquía, grafo implicativo con cuatro umbrales.
  - Cap. 11, David, Guillet, Briand, Gras, *On the use of Implication Intensity for matching ontologies and textual taxonomies*, pp. 227-245: método AROMA (futuro: proyecciones entre mundos).
- **Pazmiño, Bonilla, Baquero, Miguez.** *Software Estadístico CHIC: descubriendo sus potencialidades…* Ciencia Digital 2(4.1), 2018, pp. 122-139. Local: `194-Article Text-588-2-10-20181226.pdf`. Referencia de uso e interpretación de R-CHIC, no de algoritmo.

## Motor
- **Matrix** — `github.com/jpcosec/Matrix`, motor en `../src/`. Separación sentido/verdad (`S_i`/`V_i`) en juegos de lenguaje (`WiGame`), kernel booleano, runtime S-expr. Ver [matrix.md](matrix.md).

## Chunking
- **Korel** — `github.com/cognicore-io/korel` (Go). Pipeline de 8 fases; se copian las fases 1-3 (extract, tokenize+stopwords, multi-token longest-match). Ver [populator.md](populator.md).

## Interacción
- **Winograd, T.** *Understanding Natural Language* (1972). Fuente MACLISP del SHRDLU de consola: `sources/shrdlu/consoleshrdlu/` (módulos `NEWANS`, `SYSCOM`, `DICTIO`, `PLNR`, `SMUTIL`, `SMSPEC`, `HELP`). Ver [shrdlu.md](shrdlu.md).

## Corpus de evaluación
- **Simple English Wikipedia** — extractos vía `https://simple.wikipedia.org/w/api.php` (`prop=extracts`), **CC BY-SA 4.0**. 89 artículos de físicos nacidos 1850-1900 en `corpus/physicists/articles/`.
- **Wikipedia inglesa** — artículos completos vía `https://en.wikipedia.org/w/api.php`, **CC BY-SA 4.0**; `corpus/physicists/en/` (secciones `== H ==` → `## H`, recorte a 40 000 chars).
- **Wikidata** — hechos de referencia vía `https://query.wikidata.org/sparql`, **CC0 1.0** (`corpus/physicists/facts.jsonl`, `people.csv`).
- **GAP coreference dataset** — **Apache 2.0** (`corpus/physicists/gap-validation.tsv`, `github.com/google-research-datasets/gap-coreference`).
- `corpus/vegetales/` — corpus sintético propio (6 documentos, vocabulario semilla del paper).

## Contexto
- **Ji et al.** *Probing the Symbolic Logical Reasoning Ability of Large Language Models* (L3M), Rutgers. Local: `sources/3729238.pdf`. Referencia sobre límites de razonamiento lógico en LLMs; **no** es una fuente de CHIC (una versión anterior de este doc lo citaba así por error).
- **Wittgenstein, L.** *Tractatus Logico-Philosophicus* (1922): origen de `sinnvoll / sinnlos / unsinnig`.

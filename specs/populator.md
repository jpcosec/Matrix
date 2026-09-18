# Populator — del texto a la matriz de individuos × conceptos

Copia el front-end de [Korel](https://github.com/cognicore-io/korel) (Go) y descarta su back-end: Korel infiere con su propio motor simbólico (`is_a`, `related_to`) y un índice de recuperación; aquí eso lo hacen `sia/` y `matrix/`.

## 1. Qué se copia de Korel

| Fase Korel | Se copia | Notas |
|---|---|---|
| 1 Extract | sí | lectura de `.md/.txt`, normalización Unicode, segmentación en **oraciones** |
| 2 Tokenize + stopwords | sí | lista de stopwords por idioma con ajuste por frecuencia de dominio |
| 3 Multi-token (*greedy longest-match*) + normalización léxica | sí | n-gramas frecuentes (`"machine learning"`) como un solo concepto; lematización ligera; fold de acentos/caso |
| 4 Taxonomy tagging | no | la taxonomía la descubre CHIC |
| 5 PMI con ε-smoothing | opcional | solo como prefiltro de candidatos a multi-token; no como medida final |
| 6 Índice SQLite | no | |
| 7-8 Retrieval y *cards* | no | la explicación la da `why` sobre `Prov(f)` |

## 2. Salida (contrato con `sia/`)

```python
@dataclass(frozen=True)
class Corpus:
    X: scipy.sparse.csr_matrix        # n individuos (oraciones) × p conceptos, binaria
    concepts: list[str]               # nombre normalizado por columna
    individuals: list[Individual]     # por fila: document_id, sentence_index, char_span
    occurrences: list[Occurrence]     # (row, col, char_span) por aparición → Prov(f)
    vocab_source: dict[str, list[str]]  # concepto → formas superficiales vistas
```

- **Individuo = oración.** Mantiene `n` grande y las variables raras dentro del régimen `λ > 4`; párrafo como opción (`--unit paragraph`).
- **`occurrences` es obligatorio**: sin `char_span` no hay `Prov(f)` y el hecho no puede citarse.
- Filtros: soporte mínimo por concepto (`n_a ≥ 5`), longitud máxima de n-grama (3), stopwords, `max_concepts` (los de mayor frecuencia documental), `lang` (`es`/`en`).
- **Limpieza de boilerplate** (`clean_markdown`, activa por defecto): frontmatter YAML, bloques y código inline, URLs y rutas, marcadores de encabezado/lista/tabla, líneas `clave: valor` y de copyright se sustituyen por espacios de igual longitud, así los spans de `Prov(f)` siguen apuntando al documento (`Document.text` limpio, `Document.raw_text` original). Tokens de un solo dígito o < 3 caracteres se descartan salvo dentro de una frase multi-token.
- **Deduplicación de oraciones** (`dedupe=True`): las oraciones cuyo texto normalizado ya apareció se descartan; sin esto, una plantilla repetida (p. ej. 68 copias de la misma frase en un corpus de documentación) domina todas las reglas.

## 3. Módulo

```
populator/
  extract.py     documentos → oraciones con offsets
  tokenize.py    tokens, stopwords, normalización
  phrases.py     candidatos multi-token (frecuencia + PMI opcional), longest-match
  matrix.py      Corpus (X csr, concepts, individuals, occurrences)
tests/test_populator_*.py
```

## 4. Corpus del MVP

Recetas y descripciones de vegetales en español (dominio de `matrix/examples/vegetales*.yaml`, `colores.yaml`), ~200-500 oraciones. Los ejes de esos YAML sirven de vocabulario semilla para comprobar que el chunker recupera `lechuga, espinaca, hoja, raíz, hoja.rugosa…` y que CHIC produce `lechuga → hoja`, `zanahoria → raíz`.

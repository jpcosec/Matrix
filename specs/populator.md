# Populator — capa de signos

El populator no construye ontología: construye la **capa de signos**. Su unidad es el
**chunk** (contexto de declaración) y su producto son signos locales con offsets exactos.
Todo lo que decide significado ocurre después, en `sia/` y en el runtime. Ver
[convergence.md](convergence.md) §2.

## 1. Chunks

- `populator/extract.py::read_documents` lee `.md`/`.txt` (con `recursive=True` para árboles
  completos) y `clean_markdown` borra frontmatter, bloques de código, URLs, rutas, encabezados,
  listas y líneas `clave: valor` **conservando los offsets** (`Document.text` limpio,
  `Document.raw_text` original).
- `populator/contexts.py::chunk_documents(docs, unit="document"|"section")`:
  - `document`: un chunk por documento; `ctx_id` = stem del archivo, `title` = primer `# ` (o `""`).
  - `section`: el lead es `<stem>#0`, cada `## ` abre `<stem>#n` (las `### ` quedan dentro);
    `Chunk.title` = título del artículo y, en las secciones, `"<título> — <encabezado>"`, para que
    el nombre de la persona sea signo `name` en todas las secciones de su artículo.
  - `Chunk.metadata["article"] = stem`.
- Los encabezados se detectan en `Document.raw_text` (el limpiador conserva offsets) y el texto
  del chunk sale del texto limpio.

## 2. Signos locales

- `build_context(chunk, lang="en", max_n=3, min_count=1)` devuelve un `ContextIndex` con las
  oraciones y los signos declarados en el chunk:
  - `kind="name"`: ventanas de 1-6 tokens capitalizados que pueden contener conectores en
    minúscula (`of`, `de`, `the`, `van`, `y`, …) y posesivos (`King's`, `'t`); nunca cruzan
    puntuación (`, ; ( ) — –`) ni saltos de línea. El título del chunk también declara su nombre.
  - `kind="pronoun"`: `she/he/it/they/her/him/his/hers/their/ella/él/ellos/ellas/su`, siempre como
    pronombre, también al inicio de oración.
  - `kind="term"`: unigramas de contenido (≥ 3 letras, no función) y n-gramas (≤ `max_n`) que se
    repiten ≥ 2 veces en el chunk (`min_count`), con *longest match*.
- Un símbolo es `(signo, contexto)`: `LocalSign.symbol_id = f"{norm}@{ctx_id}"`. La normalización
  (`normalize`) solo reconoce repeticiones **dentro** del chunk: `Curie` y `curie` son el mismo
  signo local, pero `she@Q7186` y `she@Q937` son símbolos distintos. **No hay plegado de alias ni
  catálogo global de símbolos.**
- Las ocurrencias (`Occurrence(sentence_index, span)`) son spans absolutos sobre `Document.text`,
  que es lo que citan `Prov(f)` y `evidence`.

## 3. Enrutar, no identificar

`SignIndex(contexts)` da `contexts_of(norm)` y `occurrences_of(norm, ctx_id)`. Sirve para
**recuperar y enrutar** («este signo aparece en estos chunks»), nunca para decidir identidad: la
identidad entre contextos la propone la convergencia y la confirma el curado
([convergence.md](convergence.md) §3).

## 4. Qué ya no hay

La matriz índice `individuos × conceptos` (y su estructura asociada) se retiró: la unidad de
trabajo es el chunk, y las matrices que se analizan las construyen `sia/` y
`pipeline/convergence.py` a partir de las **declaraciones** de cada contexto
(`pipeline/decompose.py`), no de los signos sueltos.

# Matrix-SHRDLU — especificación

Un motor de conocimiento que **puebla** mundos lógicos desde texto crudo (chunker estadístico + CHIC, con cita de origen para cada hecho) y que se **usa** conversando como con SHRDLU (afirmar, preguntar, "¿por qué?", aclarar, definir), evaluado con álgebra booleana sobre el motor Matrix.

- [SPEC.md](SPEC.md) — visión, decisiones cerradas, alcance del MVP
- [matrix.md](matrix.md) — el motor booleano: qué se usa, qué se cambia, qué se ignora
- [populator.md](populator.md) — del texto a la matriz individuos × conceptos (Korel, fases 1-3)
- [chic.md](chic.md) — CHIC / SIA: medidas, jerarquía, grafo, contrato con Matrix (`sia/`)
- [grounding.md](grounding.md) — curado: candidatos, LLM propone, humano confirma
- [provenance.md](provenance.md) — `Fact.evidence`: citas, niveles, conflictos
- [shrdlu.md](shrdlu.md) — el loop de interacción
- [runtime_api.md](runtime_api.md) — S-expressions: verbos existentes y nuevos
- [sources.md](sources.md) — fuentes
- [appendix_causality.md](appendix_causality.md) — causalidad (futuro)

Código: `matrix/` (motor, subtree), `sia/` (CHIC), `populator/` (por hacer). Tests: `matrix/tests/`, `tests/`.

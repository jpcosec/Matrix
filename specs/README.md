# Matrix-SHRDLU — especificación

Un motor de conocimiento que **puebla** mundos lógicos desde texto crudo (chunker estadístico + CHIC, con cita de origen para cada hecho) y que se **usa** conversando como con SHRDLU (afirmar, preguntar, "¿por qué?", aclarar, definir), evaluado con álgebra booleana sobre el motor Matrix.

- [SPEC.md](SPEC.md) — visión, decisiones cerradas, alcance del MVP
- [convergence.md](convergence.md) — **diseño corregido del puente**: símbolos por contexto, taxonomía de `W_i`, rol exacto de CHIC (prevalece sobre populator/chic/grounding donde contradiga)
- [matrix.md](matrix.md) — el motor booleano: qué se usa, qué se cambia, qué se ignora
- [populator.md](populator.md) — del texto a los chunks y sus signos locales (Korel, fases 1-3)
- [chic.md](chic.md) — CHIC / SIA: medidas, jerarquía, grafo, contrato con Matrix (`sia/`)
- [grounding.md](grounding.md) — curado: candidatos, LLM propone, humano confirma
- [provenance.md](provenance.md) — `Fact.evidence`: citas, niveles, conflictos
- [shrdlu.md](shrdlu.md) — el loop de interacción
- [runtime_api.md](runtime_api.md) — S-expressions: verbos existentes y nuevos
- [sources.md](sources.md) — fuentes
- [appendix_causality.md](appendix_causality.md) — causalidad (futuro)

Código: `matrix/` (motor, subtree), `sia/` (CHIC), `populator/` (chunker), `pipeline/` (descomposición, ingesta, convergencia y CLI), `corpus/vegetales/` (corpus de prueba). Tests: `tests/` (raíz) y `matrix/tests/`. Uso: [README raíz](../README.md).

> **Documento técnico completo (estructura de paper):** [`docs/paper.md`](../docs/paper.md). Modelo, algoritmo de convergencia, ley de soporte mínimo, rediseño aglomerativo, protocolo experimental, resultados y amenazas a la validez.

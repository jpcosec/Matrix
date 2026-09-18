# Procedencia y Resolución de Conflictos (Provenance)

En un sistema que mezcla texto estadístico, deducción matricial y comprobación causal, una celda en la Matriz de Verdad ($V_i$) no puede ser solo un `1` o un `0`. Necesita trazabilidad absoluta para resolver conflictos cuando las reglas chocan.

## La Capa de Procedencia
Cada hecho o relación almacenada en el motor debe tener metadatos de linaje (Provenance). Los orígenes posibles determinan el "peso" epistémico de la afirmación:

1. **Observed (Empírico)**: Un hecho insertado directamente por telemetría o ingesta humana dura. Es la verdad absoluta.
2. **Causal (Validado)**: Reglas derivadas del cálculo `do(X)` en la base de datos transaccional ($C_i$). Tiene precedencia sobre la estadística.
3. **Inferred (Modus Ponens)**: Hecho deducido matemáticamente cruzando tensores (ej. $V_A \cdot I_{A \implies B}$).
4. **Statistical (CHIC/Korel)**: Relación extraída por minería de texto (Alta co-ocurrencia / Implicancia $I_i$). Es el nivel más débil, útil como heurística cuando no hay datos empíricos.

## Mecanismo de Resolución
Si el LLM pregunta algo y hay un conflicto entre matrices (ej. el texto estadístico asume que X implica Y, pero la matriz causal demuestra que no), el motor Matrix utiliza la etiqueta de Procedencia como mecanismo de desempate determinista (Fallback). El grafo causal sobreescribe la co-ocurrencia estadística.

# Apéndice — Causalidad (futuro: de texto a datos)

**Fuera de alcance del MVP.** Se conserva la idea para cuando el sistema trabaje también sobre datos tabulares y no solo sobre texto.

## Idea

Sentido (`S_i`) dice qué se puede decir; la convergencia (φ de CHIC) dice qué símbolos coinciden entre contextos; causalidad diría *por qué*. Como los textos confunden correlación con causa, la única forma de confirmarla es intervenir o, al menos, condicionar sobre datos duros.

## Flujo previsto

1. **Hipótesis:** una regularidad `a → b` que converge entre contextos (p. ej. `promoción → devoluciones`).
2. **Anclaje a datos:** mapear `a` y `b` a columnas/agregados de una base transaccional. Es el mismo problema de [grounding.md](grounding.md): lo propone un LLM y lo confirma un humano; no se automatiza.
3. **Prueba:** usar la jerarquía de CHIC como esqueleto a priori de una red bayesiana y validar solo sus aristas (algoritmos tipo PC, criterio de puerta trasera de Pearl): ¿sobrevive `P(b | do(a))` al condicionar por confusores (`temporada`, `categoría`)?
4. **Ascenso epistémico:** si sobrevive, el hecho sube a un nuevo `tier=causal` (entre `observed` y `confirmed`) y habilita preguntas contrafactuales ("¿si quitamos las promociones…?"). Si no, queda como `confirmed` narrativo con `evidence.causal=false`.

## Qué haría falta

- Un `tier=causal` en [provenance.md](provenance.md).
- Un módulo de anclaje texto → esquema de datos (curado).
- Un motor de inferencia causal externo (`pgmpy`, `dowhy` o similar) invocado por lotes, no en el runtime.
- No se crea ninguna matriz `C_i`: el resultado es metadata en `Fact.evidence`.

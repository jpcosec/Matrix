# Convergencia: símbolos por contexto, taxonomía de `W_i` y el rol de CHIC

Este documento corrige el diseño del puente texto → Matrix. **Sustituye** lo que `populator.md`, `chic.md` y `grounding.md` dicen sobre normalización de símbolos, candidatos `implies`/`nonsense` por co-ocurrencia y CHIC como fuente de hechos. Lo que no contradice sigue vigente.

## 1. Principios (del Tractatus y de los átomos de Matrix)

1. **El mundo es la totalidad de los hechos.** La unidad es la configuración `(R a b)`, no el objeto ni la propiedad. `hoja` es tan símbolo como `lechuga`; "objeto → propiedad" es solo el ejemplo del paper.
2. **La forma lógica (`S_i`) es a priori y estructural.** Emerge de contextos cerrados y firmas de relación al cruzarlos; no se estima por frecuencias. Ausencia de co-ocurrencia ≠ *unsinnig*.
3. **El símbolo es `(signo, contexto de declaración)`.** `she` en un artículo sobre Curie es un símbolo válido de ese contexto. No hay catálogo universal de símbolos ni plegado de alias a la entrada. Significado = uso en el juego.
4. **La desambiguación no es un paso; es el algoritmo.** Con N contextos sobre un mismo campo semántico, las configuraciones en que entra cada símbolo convergen o no. El referente es la intersección que sobrevive: la ruta del árbol de contextos donde las ocurrencias coinciden. Identidad entre contextos = proyección no vacía, propuesta por convergencia y confirmada por regla o curado; nunca coincidencia de strings.
5. **La basura se aísla con volumen.** Un hecho espurio no encuentra configuraciones compatibles en otros contextos: queda en una hoja aislada, no se proyecta, no sube de `proposed`. Un hecho real converge desde muchos contextos. La calidad sube con la cantidad.

## 2. Qué aporta cada pieza

| Pieza | Aporta | No aporta |
|---|---|---|
| **Korel / chunker** (capa de signos) | chunks = contextos observables de uso; signos locales tal cual; offsets (`Prov`); índice signo → texto; agrupación de chunks por vocabulario como *hipótesis* de dominios | símbolos globales, hechos, relaciones, sentido |
| **Descompositor** (LLM barato o heurística) | por oración, dentro de su chunk: candidatos `(R a b)` con signos locales, sin estatus de verdad | decisiones lógicas |
| **Runtime Matrix** | `WiGame` por `(contexto, R)`; chequeos de sentido (indexación por contexto, contradicción); `V_i`; deducción; proyecciones; curado con procedencia | — |
| **CHIC / `sia`** | convergencia: taxonomía de contextos, convergencia de símbolos, mantenimiento `E(R)` (§3) | hechos, sentido, relaciones, identidad |

## 3. CHIC: tres matrices, tres salidas

| Uso | Individuos (filas) | Variables (columnas) | Qué da | A dónde va |
|---|---|---|---|---|
| **Taxonomía de contextos** | contextos (chunks) | declaraciones locales (signos o `(R · b)`) | implicación `A → B` = "donde se dice A se dice B" = **anidamiento con dirección**; jerarquía cortada en niveles significativos; contribución = pertenencia | árbol `Context → subcontexto → WiGame`, `ContextRoute`/`WC_k`. Traspuesta: `ctx_A → ctx_B` = A cabe en B |
| **Convergencia de símbolos** | configuraciones en que entra un símbolo (`R`, co-participante) | símbolos `signo@ctx` | `she@art → curie@hist` con φ≈1: todo lo dicho de *she* se dice de *Curie* → proyección **con dirección**; bidireccional → `equivalent`; jerarquía = taxonomía de referentes; similitud = alias | candidatos `projection` / `equivalent`; promoción por regla de convergencia (φ, soporte, nº de contextos) o curado |
| **Mantenimiento de `W_i`** | sujetos del juego | coordenadas `(R, b)` | columnas tautológicas en un subconjunto → compuertas `C_k`; jerarquía → subjuegos; similitud → ejes y `D_i` para colisiones `W⊗Wᵀ−I` | `create context/wigame`, `RoutingProjection`, candidatos `D_i` |

Medida de confianza de la KB: cohesión y tipicidad = cuánto converge un hecho o símbolo y desde cuántos contextos. Lo aislado no se promueve.

**Bootstrap de la convergencia:** en la primera pasada, el co-participante de una configuración se identifica por su forma superficial normalizada (evidencia, no identidad); en pasadas siguientes, por el referente ya convergido. Es un punto fijo iterativo.

## 4. Flujo

```
texto ─► Korel: chunks (contextos), signos locales, offsets, índice
              │
              ▼
      descompositor por oración ─► (R a b) candidatas @chunk, con Prov
              │
              ▼
      runtime: WiGame(ctx, R) ─► sentido (indexación, contradicción) ─► V_i por contexto
              │
              ▼
      CHIC: contextos×declaraciones ─► árbol de contextos
            configuraciones×símbolos ─► proyecciones / equivalent
            sujetos×coordenadas (por W_i) ─► compuertas, subjuegos, D_i
              │
              ▼
      promoción por convergencia o curado ─► consultas ruteadas (route_search) con Prov
```

## 5. Lo que se elimina del código actual

- `pipeline/bridge.py`: relación `implies`, candidatos `fact` por arco, `nonsense` por no co-ocurrencia, `class` como lista plana.
- `populator`: normalización/alias como identidad; dedupe entre contextos (solo dentro del chunk).
- La métrica "recuperación con procedencia" como prueba de conocimiento.

## 6. Cómo se prueba (ver plan de implementación en `SPEC.md` §6)

- Corpus sintético con referentes conocidos (artículos sobre Curie y sobre Franklin usando `she`, nombres y variantes; hechos plantados falsos): el árbol agrupa los artículos correctos; `she@curie_i → curie@curie_j` se propone y `she@franklin_k` no; los hechos plantados quedan aislados.
- `corpus/vegetales`: los `W_i` resultantes reproducen la tabla del paper (hoja/raíz/tallo; lisa/rugosa como `D_i`; `verdura` como compuerta).
- Preguntas ruteadas con respuesta conocida (`W_i ⊗ v_q` a través de proyecciones), no conteo de citas.

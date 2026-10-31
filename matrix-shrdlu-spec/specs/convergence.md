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
| **Convergencia de símbolos** | configuraciones en que entra un símbolo (`R`, co-participante) | símbolos `signo@ctx` | `she@art → curie@hist` con φ≈1: todo lo dicho de *she* se dice de *Curie* → proyección **con dirección**; bidireccional → `equivalent`; jerarquía = taxonomía de referentes; similitud = alias | candidatos `projection` / `equivalent`; promoción por regla de convergencia (φ, soporte, nº de contextos) o curado; los referentes se guardan en `system.referents` / `system.equivalences` (memoria del mundo, sin kernel `p×p`) |
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

## 7. Resultados

Evaluación sobre `corpus/physicists` (89 físicos: artículo de Simple English + artículo completo de
la Wikipedia inglesa + hechos de Wikidata + GAP). Régimen `pairs` = 178 contextos (89 artículos
Simple + 89 lead EN); comando `experiments.eval_physicists --regime pairs --decomposer <modo>`, cada
corrida bajo tope de 4 GB (`scripts/capped.sh 4 -- …`). Detalle completo en
`../.herdr/llm_report.md`.

| métrica | heuristic | llm | both |
|---|---|---|---|
| declaraciones / símbolos / variables | 2 931 / 4 120 / 690 | 11 242 / 10 703 / 4 427 | 13 574 / 12 277 / 5 701 |
| pares candidatos (≥ 1 configuración compartida) | 37 | 275 | 326 |
| declaraciones por símbolo (media / mediana) | 1.42 / 1 | 2.10 / 1 | 2.21 / 1 |
| configuraciones compartidas por par correcto (media) | 0.49 | 1.28 | 1.53 |
| convergencia entre fuentes (personas) | 1/77 = 0.013 | 5/79 = 0.063 | 8/81 = 0.099 |
| intra-contexto | 0/157 | 0/158 | 0/161 |
| ranking MRR / hit@1 / hit@3 (todas las consultas) | 0.055 / 0.043 / 0.053 | 0.265 / 0.250 / 0.261 | 0.243 / 0.219 / 0.250 |
| falsas fusiones | 0 | 0 | 1 |
| QA Wikidata (recall etiqueta / con salto) | 0.002 / 0.0 | 0.011 / 0.048 | 0.012 / 0.045 |
| basura (plantada vs real aislada) | 1.0 vs 0.98 | 1.0 vs 0.96 | 1.0 vs 0.92 |
| promovidos / propuestos / referentes | 6 / 65 / 3 | 45 / 296 / 18 | 98 / 352 / 42 |
| memoria pico / tiempo | 198 MB / 2.5 s | 250 MB / 10.2 s | 274 MB / 14.4 s |

Otros regímenes: `document` sobre Simple (89 contextos, 1 488 MB → 198 MB tras el rediseño por
pares), `document` sobre EN (89 contextos, 7 921 MB → 250 MB) y `section` sobre EN (564 contextos,
3 promociones y una única fusión falsa `it@Q153238#1 ~ it@Q9123#5`, φ=0.9626).

**Diagnóstico.** El algoritmo converge en el régimen multi-fuente cuando hay **≥ 2 configuraciones
informativas compartidas**: el descompositor LLM triplica las declaraciones y multiplica por cinco
la convergencia entre fuentes (0.013 → 0.063) y por ~50 el QA con salto (0.0 → 0.048). Lo que sigue
fallando es la **capa de declaraciones**, no la promoción: los mismos hechos se lexicalizan distinto
en cada fuente (`Nobel Prize` vs `Nobel Prize in Chemistry`), la intra-contexto es 0 (pronombre y
etiqueta comparten a lo sumo 1 configuración) y el ranking acierta en el 25 % de las consultas. La
basura queda aislada siempre; con el corpus real el contraste es 1.0 vs 0.96.

## 8. Siguiente paso

1. **Canonicalización de objetos** vía `equivalent` en el kernel de símbolos (misma entidad, formas
   distintas): es el cuello de botella medido, y no requiere tocar la promoción.
2. **Más fuentes por entidad** (más de dos contextos por persona): la convergencia mejora con
   volumen por diseño; el corpus actual aporta dos contextos por físico.
3. **Descompositor LLM como default** (con la caché versionada del corpus) y la heurística como
   respaldo offline.
4. **Taxonomía a escala**: `context_taxonomy` es opcional porque `build_hierarchy` es O(p²) por nivel
   en Python; con `max_features=600` deja de ser un cuello de botella para el informe.
5. **Nunca `p×p`**: ninguna estructura puede crecer con el cuadrado del número de símbolos. Tres
   corridas sin tope murieron por OOM el 2026-09-20; por eso la intensidad se calcula sobre pares
   candidatos (índice invertido configuración → símbolos), la convergencia entra por lotes y toda
   evaluación corre bajo `bash scripts/capped.sh 4 -- …`.

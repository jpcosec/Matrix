# CHIC / SIA — el compilador ontológico

CHIC (*Cohesive Hierarchical Implicative Classification*) es el software de referencia del Análisis Estadístico Implicativo (SIA) de Régis Gras. Aquí se implementa desde cero como el paquete `sia/`, siguiendo el libro *Statistical Implicative Analysis* (Gras, Suzuki, Guillet, Spagnolo eds., SCI 127, Springer 2008): cap. 1 (Gras & Kuntz, pp. 11-40), cap. 2 (Couturier, pp. 41-53) y cap. 11 (David et al., AROMA, pp. 227-245). Páginas citadas = numeración impresa.

## 1. Por qué CHIC y no PMI

PMI mide co-ocurrencia **simétrica**. SIA mide la improbabilidad de los **contraejemplos** de `a → b` (casos con `a` y sin `b`) bajo independencia, por lo que `a → b` y `b → a` reciben valores distintos. Además organiza las reglas en una jerarquía orientada (reglas de reglas) y en un grafo. Eso es exactamente la estructura que necesita Matrix: implicaciones dirigidas para `I` y clases anidadas para partir un `WiGame` en sub-mundos.

## 2. Entrada

`X`: matriz binaria `n × p` (`scipy.sparse.csr_matrix`), **individuos** en filas y **variables** (conceptos) en columnas. La decide el [Populator](populator.md). Individuo = oración (no documento): mantiene `n` grande y las variables raras dentro del régimen de validez de la aproximación normal.

## 3. Medidas (`sia/intensity.py`, `sia/cohesion.py`)

Para `a → b`: `n_a`, `n_b`, `n_{ab}`, contraejemplos `n_{a¬b} = n_a − n_{ab}`, `n_{¬b} = n − n_b`.

- **Índice** (p. 15): `q(a,¬b) = (n_{a¬b} − λ)/√λ`, `λ = n_a·n_{¬b}/n`.
- **Intensidad clásica** (Def. 2, p. 16): `ϕ(a,b) = 1 − Pr[Q ≤ q]` con `Q ~ N(0,1)` si `λ > 4`; Poisson exacta `1 − Σ_{s≤n_{a¬b}} e^{−λ}λ^s/s!` si no. `ϕ = 0` si `n_b = n`. Admisible si `ϕ ≥ 1 − α` (Def. 3).
- **Versión entrópica** (§3.4, pp. 20-22), la que se usa para texto: entropías condicionales `H_{b/a}` (dado `a`) y `H_{a/b}` (dado `¬b`); `I^α = 1 − H^α` si los contraejemplos son menos de la mitad del soporte, `0` si no; índice de inclusión `τ = (I^α_{b/a}·I^α_{a/b})^{1/2α}`; **`φ = (ϕ·τ)^{1/2}`**, con **`α = 2`** (reproduce `τ = 0.6035` de la Tabla 1b, p. 22).
- **Cohesión** (Def. 7, p. 25): `c(a,b) = (1 − H(ϕ)²)^{1/2}` si `ϕ > 0.5`, `0` si no. Para una clase `(v_1…v_r)`: media geométrica de `c(v_i,v_j)` sobre los pares ordenados `i < j` (Def. 8).

Valores de control (Tabla 1, p. 22): (a) `n=4000, n_a=600, n_b=800, n_{ab}=200` → `ϕ=0.9999, τ=0, φ=0`; (b) `n_b=1400, n_{ab}=400` → `ϕ=1, τ=0.6035, φ=0.777`.

## 4. Estructuras (`sia/hierarchy.py`, `sia/graph.py`)

- **Jerarquía implicativa** (Def. 9 y §6.3, pp. 26-28): aglomerativa; en cada nivel se une el par de clases de máxima cohesión; se detiene cuando todas las cohesiones candidatas son 0; altura `h = 1 − c` (ultramétrica). La clase `aed` con `ed` ya formada se lee `a → (e → d)`.
- **Niveles significativos** (§7.2, pp. 29-30, criterio de Lerman): concordancia entre el preorden por cohesión y la partición amalgamados/separados; nivel significativo = máximo local del estadístico `s_k`.
- **Grafo implicativo** (cap. 2 §5, p. 49): arcos `φ ≥ θ` para `θ ∈ {0.99, 0.95, 0.90, 0.85}`; no es transitivo por construcción (p. 34); clausura y reducción transitiva se calculan aparte.

## 5. Salida y contrato con Matrix (`sia/report.py`)

| Salida de `sia/` | Destino en Matrix | Estado inicial |
|---|---|---|
| Conceptos (columnas de `X`) | `(create symbol <id> <sign>)` | — |
| Arcos `a → b` con `φ ≥ φ_r` | Filas de la Implication Matrix `I` (`kernel/rule_matrix.py`) como `(if a b)` | `tier=statistical`, `truth=UNKNOWN`, con `Prov(f)` |
| Clase de un nivel significativo | Dimensión de partición `C_k` → `WiGame` hijo con los símbolos de la clase + `RoutingProjection` `WC` al padre | `tier=statistical` |
| Pares que nunca co-ocurren con soporte suficiente (`n_a, n_b ≥ n_min`, `n_{ab} = 0`) | Candidatos a `unsinnig` en `S_i` | requieren curado: el silencio del corpus no es absurdo |

Todo pasa por la [cola de curado](grounding.md). Nada escribe `TRUE` en `V_i` ni `unsinnig` en `S_i` sin confirmación.

## 6. Parámetros

| Parámetro | Valor MVP | Nota |
|---|---|---|
| Medida | entrópica, `α = 2` | clásica disponible para `n < 300` |
| `α_adm` | 0.05 (`ϕ ≥ 0.95`) | Def. 3 |
| Umbrales del grafo | `{0.99, 0.95, 0.90, 0.85}` | los cuatro de CHIC |
| Grado máximo de R-regla | 1 para el puente a `I`; la jerarquía se calcula completa | grado > 1 = trabajo futuro |
| `n_min` para `unsinnig` | 20 | a calibrar |

## 7. Implementado además

- **AROMA** (cap. 11, `sia/aroma.py`): dadas dos jerarquías `H = (C, ≤, T, γ)`, reglas `a → b` entre nodos significativas si `ϕ ≥ ϕ_r` y máximas frente a ancestros de `a` / descendientes de `b`. `pipeline/match.py` las convierte en candidatos `projection` entre dos `WiGame`. Nota estructural: ninguna regla hacia la raíz de `H₂` puede ser significativa (`n_b = n ⇒ ϕ = 0`).
- **Árbol de similitud** (cap. 2 §4, `sia/similarity.py`): índice de Lerman `s = Pr[Poisson(λ) < n_ab]`, aglomerativo no orientado; comparte `Level` y `significant_levels`.
- **Niveles significativos vectorizados**: `O(m log m)` por nivel con `searchsorted` (antes `O(p³)` en Python: p=150 → 51 s; ahora p=800 → 0.5 s).

## 8. Trabajo futuro

- Tipicidad y contribución (cap. 1 §8): qué individuos (oraciones) sostienen una regla — refuerza `Prov(f)`.
- Reglas conjuntivas estadísticas `A ∧ B → C` (Apriori + criterio de originalidad, cap. 2 §3). Las conjuntivas *ground* ya existen en el runtime (`define` con `and`).
- Versión entrópica del índice de similitud.

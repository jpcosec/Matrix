# SHRDLU-Matrix: Especificación de Arquitectura

## 1. Visión General
SHRDLU-Matrix reimagina el motor lógico de Terry Winograd (Micro Planner) reemplazando la búsqueda recursiva en árboles (backtracking) por **álgebra lineal booleana**. Al montar el razonamiento sobre la arquitectura `Matrix` (Índice Mínimo Aglomerativo de Recuperación de Texto), el sistema logra deducciones en tiempo $O(1)$ o $O(\text{profundidad})$, eliminando la falsedad por ignorancia y operando a velocidades de hardware acelerado (JAX).

El LLM actúa exclusivamente como traductor de lenguaje natural a "Metas Lógicas" (Vectores de Búsqueda), mientras que el motor Matrix evalúa el *Sentido* ($S_i$) y la *Verdad* ($V_i$) mediante multiplicaciones matriciales.

---

## 2. Ontología y Estructuras de Datos

En lugar de almacenar hechos como listas `(COLOR BLOQUE ROJO)`, el mundo se representa como tensores dentro de contextos locales cerrados.

### 2.1 El Espacio Lógico (`WiGame`)
Cada dominio (ej. Mundo de los Bloques, Restaurante, Código Fuente) es un `WiGame` independiente. Esto encapsula el vocabulario y evita que la semántica se contamine globalmente.

### 2.2 Las Matrices de Estado
Para cada relación $R$ en un `WiGame`, existen dos matrices (o tensores) de dimensiones $A \times B$ (donde $A$ y $B$ son los términos admisibles):

1. **La Matriz de Sentido ($S_i$)**:
   Una matriz categórica que define el estado semántico de la proposición $aRb$:
   - `1` (`sinnvoll`): La proposición tiene sentido y puede ser evaluada.
   - `0` (`sinnlos`): Tautología o contradicción estructural (vacía).
   - `-1` (`unsinnig`): Absurdo gramatical o semántico (ej. "El color rojo pesa 5 kilos").

2. **La Matriz de Verdad ($V_i$)**:
   Una matriz booleana (densa o rala) que define el estado de los hechos factibles:
   - `1` (True): El hecho está comprobado en el mundo.
   - `0` (False): El hecho no ocurre.

---

## 3. El Pipeline de Ejecución (El "Micro Planner" Matricial)

El flujo de una orden humana (ej. *"Mueve todos los bloques rojos que estén sobre la mesa"*) sigue un camino estrictamente matricial.

### Fase 1: Traducción a Vector de Búsqueda (`SearchVector`)
El LLM recibe la instrucción y la traduce a una meta lógica. No programa loops, simplemente emite el estado deseado:
`GOAL: FIND ?x WHERE (AND (COLOR ?x RED) (ON ?x TABLE))`

### Fase 2: Validación de Sentido (El Linter de Wittgenstein)
Antes de buscar datos, el motor Matrix convierte la query en una "Máscara de Sentido".
Se consulta $S_{color}(?, ROJO) \land S_{on}(?, MESA)$.
* Si el resultado es una matriz de puros ceros (`unsinnig`), el motor aborta en $O(1)$ y responde al LLM: *"La consulta carece de sentido lógico en este WiGame"*.

### Fase 3: Deducción por Modus Ponens Vectorizado
Si la consulta es `sinnvoll`, se ejecuta contra $V_i$.
En Micro Planner, el motor buscaría bloque por bloque usando backtracking. En Matrix, es álgebra pura:
1. $Vec_{rojos} = V_{color} \cdot Vector_{ROJO}$
2. $Vec_{sobre\_mesa} = V_{on} \cdot Vector_{MESA}$
3. $Vec_{resultado} = Vec_{rojos} \odot Vec_{sobre\_mesa}$ (Multiplicación elemento a elemento / AND lógico).

**Resultado**: En 3 operaciones vectorizadas ejecutadas en GPU/CPU vía JAX, el sistema encuentra instantáneamente todas las entidades que cumplen la condición, sin importar si hay 10 o 1,000,000 de bloques.

### Fase 4: Teoremas Dinámicos como Multiplicación de Adyacencia
Si la regla requiere deducción profunda (ej. *"Bloques soportados indirectamente por la mesa"*), en lugar de recursión infinita, se utiliza la matriz de adyacencia de soporte $A$:
$Vec_{soportados} = Vector_{MESA} \cdot (A + A^2 + A^3 + ... + A^n)$
El cierre transitivo se calcula matemáticamente, resolviendo el clásico problema de profundidad de búsqueda en un solo cálculo algebraico.

---

## 4. Cross-Context Routing (`RoutingProjection`)

A diferencia de SHRDLU, que vivía en un solo mundo monoteísta, SHRDLU-Matrix permite el razonamiento multi-dominio.

Si el LLM pide *"Notifica a los dueños de las mesas ocupadas"*:
1. En el `WiGame_Restaurante`, se calcula el vector de Mesas Ocupadas ($Vec_{ocupadas}$).
2. Se aplica una matriz de proyección $\mathbf{P}$ (`RoutingProjection`) que mapea el eje de entidades "Mesas" al eje "Dueños" en el `WiGame_Cobranza`.
3. $Vec_{notificar} = Vec_{ocupadas} \cdot \mathbf{P}$
4. La deducción cruzó de un juego de lenguaje a otro sin perder determinismo y sin usar lógica difusa.

---

## 5. Ventajas sobre el paradigma tradicional

1. **Eficiencia Computacional:** La inferencia lógica abandona las listas enlazadas (LISP) y el backtracking escalar, adoptando BLAS/JAX. Es el matrimonio perfecto entre el rigor simbólico y la velocidad de las redes neuronales.
2. **Defensa contra Alucinaciones:** El LLM no puede "engañar" al motor. Si inventa una relación irreal, $S_i$ la aplasta instintivamente devolviendo `unsinnig`.
3. **Escalabilidad:** Evaluar una regla sobre 100,000 documentos cuesta casi lo mismo que evaluarla sobre 10, porque las operaciones booleanas se empaquetan en bits.

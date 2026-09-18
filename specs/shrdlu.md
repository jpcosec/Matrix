# SHRDLU (La Interfaz Orientada a Metas)

SHRDLU actúa como la capa superior de interacción humana y resolución lógica. Reimagina el Micro Planner original (lenguaje deductivo de resolución de metas) pero ejecutándose algebraicamente sobre las matrices de Matrix.

## El LLM como Traductor
El usuario habla en lenguaje natural. El LLM **no busca en la base de datos ni deduce la lógica**; su único rol es traducir la intención ambigua del usuario a un vector de meta formal (`SearchVector` o Metas S-Expr).

## El Micro Planner Matricial
En vez de hacer backtracking recursivo iterando punteros en un grafo lógico plano (el gran cuello de botella del Prolog y Planner de los 70s):
1. **Linter de Sentido (Wittgenstein)**: Pasa el vector de búsqueda por la matriz $S_i$. Si intersecta una celda `unsinnig` (absurdo/sin sentido), el motor rechaza el comando en $O(1)$ y educa al LLM sobre el error semántico.
2. **Modus Ponens Vectorizado**: Ejecuta las reglas de deducción multiplicando los tensores de verdad ($V_i$). 
3. **Consultas Complejas (Deep Traversal)**: Una cadena de implicaciones se resuelve algebraicamente sumando potencias de la matriz de adyacencia generada por CHIC. Esto cruza los mundos lógicos ($W_i$) de forma rápida y matemáticamente inmune a las alucinaciones.

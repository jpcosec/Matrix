# Causalidad y Redes Bayesianas

Si el *Sentido* define lo que se puede decir, y la *Implicancia* define lo que suele ocurrir junto, la **Causalidad** define *por qué* ocurren las cosas. 

Añadir Grafos Causales (Redes Bayesianas y cálculo `do(X)` de Judea Pearl) convierte al motor matricial en una herramienta capaz de hacer razonamiento contrafactual.

## La Tríada del Razonamiento
1. **Sentido ($S_i$)**: Extraído del texto. "¿Es lógico cruzar la variable 'Color' con 'Número'?"
2. **Implicancia ($I_i$)**: Extraído del texto mediante CHIC. "Los textos muestran que A siempre va de la mano con B".
3. **Causalidad ($C_i$)**: Comprobada empíricamente. "Si yo *intervengo* A (acción), ¿B cambia realmente, o solo estaban correlacionados por una variable C?".

## El Flujo Híbrido (Texto $\rightarrow$ Datos)
Como la causalidad no se puede confirmar leyendo texto (los textos suelen confundir correlación con causalidad), el sistema utiliza un flujo híbrido:

1. **Generación de Hipótesis**: CHIC extrae un grafo jerárquico de implicaciones desde los documentos. Por ejemplo: `(Campaña Marketing) \implies (Aumento de Ventas)`.
2. **Anclaje a Datos Duros**: El motor lee qué tablas o bases de datos relacionales ("datos que los textos referencian", como `dataset.xlsx`) están asociadas a esos conceptos.
3. **Prueba Causal**: El motor ejecuta algoritmos de inferencia causal (Redes Bayesianas) sobre los datos duros numéricos para verificar si existe una dependencia condicional real (ej. descartar que la estacionalidad sea la verdadera causa del aumento de ventas).
4. **Actualización de la Matriz**: Si la causalidad se comprueba, la flecha de implicación se asciende a un enlace causal rígido en el motor Matrix, permitiendo que el LLM responda preguntas del tipo: *"¿Qué pasaría si...? (What-if)"*.

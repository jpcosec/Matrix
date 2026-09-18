# Superficie de Ejecución (Runtime API)

El motor necesita una interfaz determinista para mutar los estados de las matrices. El lenguaje natural es para el usuario, pero el motor (y el LLM actuando como operador) debe compilar todo a comandos estrictos.

## Sintaxis de S-Expressions
Basado en el diseño original de Matrix, las operaciones de ingesta, deducción y enrutamiento se exponen como S-expressions (LISP-like). Esto evita errores de parsing y asegura que las mutaciones sean atómicas.

### Comandos Core
- **Definición Ontológica (Generando ejes en $S_i$)**:
  `(create symbol table mesa)`
  `(create relation assigned_to)`
  `(create li li:restaurant assigned_to (axis-a client) (axis-b table))`

- **Instanciación de Mundos**:
  `(create wigame wigame:local_1 li:restaurant)`

- **Mutación de Hechos (Poblando $V_i$)**:
  `(assert wigame:local_1 (assigned_to client_1 table_5))`
  `(retract wigame:local_1 (assigned_to client_1 table_5))`

- **Consultas y Deducciones (Ejecutando Álgebra)**:
  `(check wigame:local_1 (assigned_to ?x table_5))` -> Compila a una multiplicación vectorial contra la columna `table_5` en la matriz.

Esta superficie asegura que cualquier agente o script pueda interactuar con el hipertensor usando primitivas estables, independientemente de cómo se generó el grafo de implicación subyacente.

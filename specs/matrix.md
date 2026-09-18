# El Motor Matrix ($W_i$, $S_i$, $V_i$)

La capa base de almacenamiento e inferencia no es un grafo de nodos y punteros, sino un **Hipertensor disperso (Sparse Hypertensor)**.

## El Campo Semántico ($A$)
Un sujeto $a$ no es un simple string. Se define como la probabilidad del signo lingüístico dado un contexto: $A = P(\text{contexto}, \text{signo})$. El mismo texto ("perro") representa vectores distintos si se evalúa en $W_{mascotas}$ vs $W_{calle}$.

## Matrices de Estado
Para cada contexto lógico ($W_i$, o "Juego de Lenguaje"), las relaciones ($aRb$) se representan en matrices/tensores:
1. **Matriz de Sentido ($S_i$)**: Define la topología del mundo. Marca si la relación $aRb$ es `sinnvoll` (tiene sentido), `sinnlos` (tautología) o `unsinnig` (absurdo).
2. **Matriz de Verdad ($V_i$)**: Almacena los hechos comprobados como valores booleanos (densos o dispersos).

## Jerarquía de Relaciones ($L_i$)
Las relaciones no son planas. Existen interfaces lógicas ($L_i$) jerárquicas. Por ejemplo, $L_{propiedad\_verdura}$ es un subconjunto de $L_{propiedades}$.
Consultar una regla abstracta equivale a hacer un "slice" o un barrido jerárquico en el eje de relaciones del hipertensor, calculado eficientemente con operaciones vectorizadas (JAX/NumPy).

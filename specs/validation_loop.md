# El Loop de Validación (De Texto a Datos Causales)

Para que el motor de inferencia matricial no sea víctima de correlaciones espurias documentadas en el texto, se implementa un loop de validación empírica. Este proceso toma las hipótesis descubricas por CHIC y las somete a prueba usando inferencia causal sobre las bases de datos transaccionales.

## Arquitectura del Loop de Validación

### Fase 1: Anclaje Semántico (Entity Grounding)
Para que el texto y los datos numéricos hablen el mismo idioma, se requiere una capa de mapeo.
- **El Hallazgo Textual**: CHIC descubre una implicación estadística en los reportes: `(Alta Promoción) \implies (Alta Tasa de Devoluciones)`.
- **El Anclaje**: El motor traduce estos nodos de texto a identificadores de datos reales (ej. `Alta Promoción` se mapea a `table: sales, column: discount_pct > 20%`. `Alta Tasa de Devoluciones` se mapea a `table: returns, aggregate: count / total_sales`).

### Fase 2: Construcción del Grafo Priori
La estructura jerárquica generada por CHIC se inyecta como un **Priori Estructural** en la Red Bayesiana. 
El algoritmo de causalidad no tiene que buscar a ciegas entre millones de combinaciones posibles en la base de datos (lo cual es un problema NP-Duro); CHIC ya le entregó el esqueleto del grafo. El motor solo tiene que validar los bordes (edges) de ese esqueleto.

### Fase 3: Pruebas de Independencia Condicional (Do-Calculus)
El motor interroga la base de datos (ej. mediante algoritmos como PC o calculando el criterio de la puerta trasera de Judea Pearl) para aislar la variable.
- Se buscan variables confusoras o variables latentes dentro del mismo $W_i$ (ej. `Categoría del Producto`, `Temporada`).
- Se calcula si la probabilidad condicional sobrevive al ajuste: $P(\text{Devoluciones} \mid \text{Promoción}) \neq P(\text{Devoluciones} \mid do(\text{Promoción}))$. 
- Si al condicionar por `Temporada`, la relación entre Promoción y Devoluciones colapsa a 0, se descarta la causalidad.

### Fase 4: Ascenso Epistémico (Actualización del Matrix Engine)
El resultado del test empírico actualiza el estado de la relación en el motor Matrix:
- **Rechazo (Correlación Espuria)**: La relación se mantiene solo como una co-ocurrencia narrativa en $I_i$, pero se marca como causalmente nula en la matriz causal ($C_i$).
- **Aprobación (Ley Causal)**: La relación asciende de nivel. Se inyecta un `1` en la celda de la matriz causal ($C_i$). 

Al tener la matriz $C_i$ activa, el LLM ahora puede responder de forma determinista y matemática a consultas contrafactuales: *"Si quitamos las promociones, ¿bajarán las devoluciones?"*.

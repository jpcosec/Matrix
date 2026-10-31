# Data Models (Materialized View)

> **⚠️ AVISO DE ARQUITECTURA:** Este documento de diseño ha sido atomizado y migrado al SSOT. 
> La Base de Datos de Hechos y los modelos operacionales ya NO se definen aquí de forma monolítica.
> La fuente de la verdad para el diseño reside ahora en los grafos de `TractatusKnowledgeMachine/atoms/`.

Este documento sirve como índice materializado de las estructuras de datos operacionales del framework Matrix.

## Modelos Centrales (SSOT Links)
* [[Hipertensor_Canonico]]: La base de datos central de hechos en memoria (Tensor JAX).
* [[WiGame]]: La proyección local del juego de lenguaje (una vista del hipertensor).
* [[LogicalSystem]]: El orquestador raíz y registro de diccionarios.
* [[Proposition]]: La estructura lógica canónica `(R a b)`.
* [[Fact]]: La proposición con valor de verdad empírico.
* [[Symbol]]: Entidad lógica que define los ejes del tensor.
* [[Thing]]: El par operacional símbolo-nombre.
* [[Relation]]: El operador lógico (eje Y del tensor).

*(Para ver los detalles formales, relaciones 5W1H+ y reglas de diseño, dirígete a los archivos `.md` correspondientes en `TractatusKnowledgeMachine/atoms/Computacion/Modelos_Datos_MEEL/`)*

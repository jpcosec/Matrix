# Data Models

El motor Matrix utiliza estructuras de datos tipadas para representar el mundo lógico.

## Context
Representa un espacio lógico $W_i$. Contiene los ejes X (Objetos) e Y (Propiedades) y sus metadatos.
- **Source**: [`Context` en src/unified_engine.py](../src/unified_engine.py)

## Bridge
Define el ruteo entre dos contextos. Permite el flujo de información de un espacio a otro.
- **Source**: [`Bridge` en src/unified_engine.py](../src/unified_engine.py)

## SymbolRegistry
El corazón del átomo *Signo vs Símbolo*. Mantiene el mapeo dinámico entre IDs internos y variantes lingüísticas.
- **Source**: [`SymbolRegistry` en src/unified_engine.py](../src/unified_engine.py)

## TruthValue
Enumeración de los estados de verdad en el motor (TRUE, FALSE, UNKNOWN, NOT_APPLICABLE).
- **Source**: [`TruthValue` en src/unified_engine.py](../src/unified_engine.py)

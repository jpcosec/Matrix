# Architecture: The 4-Layered Inversion Engine

La arquitectura TKM se basa en la segregación de responsabilidades lógicas en contextos especializados ($W_i$). Para permitir la **Inversión Descriptiva** (reconstrucción de texto desde matrices), el sistema utiliza cuatro capas fundamentales.

## Diagrama de Flujo Lógico

```text
[ Lenguaje Natural ] 
      |
      v
[ LLM Orchestrator ] --> [ W_lexicon ]   (Mapeo Signo-Símbolo)
      |              --> [ W_syntax ]    (Reglas Gramaticales)
      |              --> [ W_structure ] (Moldes Sintácticos)
      v              --> [ W_facts ]     (Verdad Factual M)
[ JAX Matrix Engine ]
```

## Las 4 Capas (Wi Contexts)

1. **W_lexicon**: Gestiona el átomo *Signo vs Símbolo*. Asocia IDs lógicos con sus representaciones literales exactas.
   - Ref: [`SymbolRegistry` en src/unified_engine.py](../src/unified_engine.py)

2. **W_syntax**: Almacena las restricciones de concordancia y categorías gramaticales (POS tags, Género, Número).
   - Ref: [`Context` en src/unified_engine.py](../src/unified_engine.py)

3. **W_structure**: Actúa como el plano de construcción. Guarda el orden secuencial y el `TEMPLATE` de la proposición original.
   - Ref: [`Bridge` en src/unified_engine.py](../src/unified_engine.py)

4. **W_facts**: La capa MEEL pura. Almacena hechos binarios sobre los que operan las máscaras estructurales ($V_i, S_i, O_i, D_i$).
   - Ref: [`UnifiedMatrixEngine` en src/unified_engine.py](../src/unified_engine.py)

## Ruteo de Inversión
La reconstrucción se realiza mediante un ruteo multi-hop orquestado por la **Omnirepresentación**, viajando desde el hecho factual hacia atrás hasta el signo léxico.

# Operations: Logical Reasoning & Text Reconstruction

Guía sobre cómo operar el motor TKM/MEEL.

## 1. Ingesta No Determinística
A través del orquestador, el motor utiliza LLMs para proyectar texto hacia las 4 capas.
- **Flujo**: Identidad -> Similitud Semántica -> Expansión.
- **Ref**: [`TKMOrchestrator` en src/tkm_orchestrator.py](../src/tkm_orchestrator.py)

## 2. Validación de Estatus (Sinnvoll/Sinnlos/Unsinnig)
El método `get_status` evalúa una coordenada lógica contra las máscaras estructurales.
- **Ref**: [`get_status` en src/unified_engine.py](../src/unified_engine.py)

## 3. Inversión Descriptiva (Reconstrucción)
Para reconstruir texto, se utiliza un proceso de ruteo inverso:
1. Localizar hecho en `W_facts`.
2. Recuperar plantilla en `W_structure`.
3. Aplicar reglas en `W_syntax`.
4. Extraer signos en `W_lexicon`.
- **Demo**: [`tests/test_tkm_roundtrip_suite.py`](../tests/test_tkm_roundtrip_suite.py)

## 4. Visualización
Exportación de matrices y árboles a formatos `spec2viz` (YAML/PlantUML).
- **Ref**: [`TKMVisualizer` en src/unified_engine.py](../src/unified_engine.py)

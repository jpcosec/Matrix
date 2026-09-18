# Populator (El Chunker Estadístico)

Basado en la arquitectura de [Korel](https://github.com/cognicore-io/korel), el poblamiento del sistema comienza procesando texto no estructurado.

## N-Gramas y Co-ocurrencias
En lugar de depender de LLMs para extraer datos a ciegas (lo cual es lento y propenso a alucinaciones), se utiliza procesamiento de lenguaje natural estadístico (ej. PMI - Pointwise Mutual Information).

## El Chunker
1. **Extracción de Conceptos**: Identifica N-gramas compuestos (ej. "machine learning") como una sola entidad semántica en lugar de tokens sueltos.
2. **Filtrado de Ruido**: Ignora stopwords y ajusta pesos según la frecuencia del dominio.
3. **Matriz Documento-Concepto**: Convierte el corpus de texto en una matriz binaria o de frecuencias, donde las filas son los contextos (oraciones/documentos) y las columnas los conceptos descubiertos. Esta matriz binarizada es el input obligatorio para el motor de implicación (CHIC).

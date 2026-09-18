# CHIC (Statistical Implicative Analysis)

CHIC (Cohesive Hierarchical Implicative Classification) es el "Compilador Ontológico". Toma la matriz plana generada por el Populator y descubre la estructura lógica y jerárquica del mundo basándose en estadística dura.

## Extracción de Implicaciones
Mientras que métodos como PMI solo encuentran co-ocurrencia simétrica, CHIC descubre asimetrías estadísticas: $A \implies B$. Si "tomate" implica fuertemente "verdura", CHIC establece una regla lógica direccional.

## Generación de $W_i$ y Jerarquías de Relación ($L_i$)
1. **Clustering Cohesivo**: CHIC agrupa conceptos que se comportan igual en el texto formando **árboles jerárquicos**.
2. **Instanciación de Mundos**: Cada rama o sub-árbol cohesivo descubierto por CHIC se puede instanciar automáticamente como la ontología de un nuevo $W_i$ (WiGame).
3. **El Eje de Relaciones ($L_i$)**: CHIC agrupa también los comportamientos de los verbos/relaciones. Si las propiedades de verduras y carnes operan distinto pero comparten una super-estructura, CHIC arma el árbol de relaciones ($L_{propiedad\_verdura} \subset L_{propiedades}$).
4. **Proyecciones de Enrutamiento**: Los enlaces de implicación que cruzan entre diferentes ramas del árbol se convierten en las autopistas lógicas (`RoutingProjections`) que conectan los diferentes sub-mundos $W_i$.

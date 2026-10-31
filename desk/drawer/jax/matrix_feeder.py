# Draft: MatrixFeeder Protocol
from abc import ABC, abstractmethod

class MatrixFeeder(ABC):
    """
    Protocolo abstracto de ingesta. Convierte estructuras del mundo real
    directamente en coordenadas tensoriales del Hipertensor Canónico.
    """
    
    def __init__(self, hypertensor):
        self.db = hypertensor
        
    @abstractmethod
    def feed_schema(self, schema_data):
        """
        Puebla el espacio lógico L_i. Declara qué símbolos y relaciones existen.
        Define las reglas de Sentido (S_i).
        """
        pass
        
    @abstractmethod
    def feed_rules(self, rules_data):
        """
        Puebla la lógica. Traduce p => q en las matrices de incidencia I, C+, C-.
        """
        pass

    @abstractmethod
    def feed_facts(self, facts_data):
        """
        Inyecta la verdad empírica (V_i) llamando a self.db.upsert_fact().
        Ojo: Internamente aplica optimización de entropía para hechos de ruteo.
        """
        pass

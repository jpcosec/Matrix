"""Statistical Implicative Analysis core (Gras & Kuntz; Couturier, SCI 127, 2008)."""

from .aroma import Hierarchy, aroma, hierarchy_from_levels
from .cohesion import cohesion_class, cohesion_pair
from .contingency import Contingency, contingency
from .graph import implicative_graph, transitive_closure
from .hierarchy import Level, build_hierarchy, classes, significant_levels
from .intensity import confidence, inclusion_index, phi_classical, phi_entropic
from .report import hierarchy_report, rules
from .similarity import build_similarity_tree, similarity_class, similarity_index

__all__ = [
    "Contingency",
    "Hierarchy",
    "Level",
    "aroma",
    "build_similarity_tree",
    "hierarchy_from_levels",
    "similarity_class",
    "similarity_index",
    "build_hierarchy",
    "classes",
    "cohesion_class",
    "cohesion_pair",
    "confidence",
    "contingency",
    "hierarchy_report",
    "implicative_graph",
    "inclusion_index",
    "phi_classical",
    "phi_entropic",
    "rules",
    "significant_levels",
    "transitive_closure",
]

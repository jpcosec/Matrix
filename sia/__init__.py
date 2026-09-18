"""Statistical Implicative Analysis core (Gras & Kuntz; Couturier, SCI 127, 2008)."""

from .cohesion import cohesion_class, cohesion_pair
from .contingency import Contingency, contingency
from .graph import implicative_graph, transitive_closure
from .hierarchy import Level, build_hierarchy, classes, significant_levels
from .intensity import confidence, inclusion_index, phi_classical, phi_entropic
from .report import hierarchy_report, rules

__all__ = [
    "Contingency",
    "Level",
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

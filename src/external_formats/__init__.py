"""External format converters for Matrix.

This package provides optional interface modules that translate between
Matrix's internal representation and standard external knowledge
representation formats (OWL, UNL, etc.).  Each converter follows the
SHRDLU prototype pattern: it lowers an external format into s-expressions
that can be fed to ``SExpressionRuntime.evaluate()``.

All converters are pure add-ons.  They depend *only* on Python stdlib;
richer backends (e.g. rdflib for OWL) are optional and detected at
runtime.
"""

from . import owl, unl

__all__ = [
    "owl",
    "unl",
]

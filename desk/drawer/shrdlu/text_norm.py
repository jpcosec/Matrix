"""Text normalisation for the SHRDLU prototype.

Vendored from `populator.tokenize` in the matrix-shrdlu-spec sibling so the
prototype has no dependency on the unported outer layer. Stdlib only.
"""

from __future__ import annotations

import unicodedata

_ALLOWED = set("abcdefghijklmnopqrstuvwxyz0123456789- ")


def normalize(text: str) -> str:
    """Lowercases, strips accents and keeps only ``[a-z0-9- ]``."""

    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in without_marks.lower() if char in _ALLOWED)


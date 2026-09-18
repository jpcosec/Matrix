"""Small identifier helpers shared inside the operational model package."""

from __future__ import annotations

import uuid


def new_id(prefix: str) -> str:
    """Builds a short deterministic-looking runtime identifier prefix."""

    return f"{prefix}:{uuid.uuid4().hex[:12]}"

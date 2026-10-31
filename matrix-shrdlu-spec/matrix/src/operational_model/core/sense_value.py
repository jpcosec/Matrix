"""Sense value enumeration for propositions."""

from __future__ import annotations

from enum import Enum


class SenseValue(str, Enum):
    """Enumerates proposition sense states inside a WiGame."""

    SINNVOLL = "sinnvoll"
    SINNLOS = "sinnlos"
    UNSINNIG = "unsinnig"

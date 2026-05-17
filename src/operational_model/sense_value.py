from __future__ import annotations

from enum import Enum


class SenseValue(str, Enum):
    SINNVOLL = "sinnvoll"
    SINNLOS = "sinnlos"
    UNSINNIG = "unsinnig"

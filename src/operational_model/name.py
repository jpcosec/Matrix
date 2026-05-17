from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Name:
    sign: str
    namespace: str = "default"

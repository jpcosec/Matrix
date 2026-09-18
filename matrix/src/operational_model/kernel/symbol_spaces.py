"""Kernel-level symbol spaces for typing and normalization."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SymbolSpace:
    """Tracks class membership and equivalence normalization."""

    instances_by_class: dict[str, set[str]] = field(default_factory=dict)
    canonical_by_symbol: dict[str, str] = field(default_factory=dict)

    def canonicalize(self, symbol: str) -> str:
        current = self.canonical_by_symbol.get(symbol, symbol)
        if current == symbol:
            return current
        canonical = self.canonicalize(current)
        self.canonical_by_symbol[symbol] = canonical
        return canonical

    def assert_equivalent(self, left: str, right: str) -> str:
        left_canonical = self.canonicalize(left)
        right_canonical = self.canonicalize(right)
        canonical = min(left_canonical, right_canonical)
        for symbol in {left, right, left_canonical, right_canonical}:
            self.canonical_by_symbol[symbol] = canonical
        self._normalize_instance_sets()
        return canonical

    def assert_instance(self, member: str, class_symbol: str) -> tuple[str, str]:
        canonical_member = self.canonicalize(member)
        canonical_class = self.canonicalize(class_symbol)
        self.instances_by_class.setdefault(canonical_class, set()).add(canonical_member)
        return canonical_member, canonical_class

    def instances_of(self, class_symbol: str) -> tuple[str, ...]:
        canonical_class = self.canonicalize(class_symbol)
        return tuple(sorted(self.instances_by_class.get(canonical_class, set())))

    def are_equivalent(self, left: str, right: str) -> bool:
        return self.canonicalize(left) == self.canonicalize(right)

    def _normalize_instance_sets(self) -> None:
        normalized: dict[str, set[str]] = {}
        for class_symbol, members in self.instances_by_class.items():
            canonical_class = self.canonicalize(class_symbol)
            normalized.setdefault(canonical_class, set()).update(
                self.canonicalize(member) for member in members
            )
        self.instances_by_class = normalized

"""Stable semantic frames for the proto-SHRDLU language layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EntityDescriptor:
    """Normalized noun-phrase descriptor."""

    determiner: str | None = None
    adjectives: tuple[str, ...] = ()
    noun: str | None = None
    referent: str | None = None

    def to_sexpr(self) -> str:
        """Serializes the descriptor to a stable s-expression-like form."""

        parts = ["entity"]
        if self.determiner:
            parts.append(f"(det {self.determiner})")
        for adjective in self.adjectives:
            parts.append(f"(adj {adjective})")
        if self.noun:
            parts.append(f"(noun {self.noun})")
        if self.referent:
            parts.append(f"(ref {self.referent})")
        return f"({' '.join(parts)})"


@dataclass(frozen=True)
class RelationFrame:
    """Normalized relation phrase."""

    relation: str
    target: EntityDescriptor

    def to_sexpr(self) -> str:
        """Serializes the relation phrase."""

        return f"(relation {self.relation} {self.target.to_sexpr()})"


@dataclass(frozen=True)
class SemanticFrame:
    """Base frame with stable serialization."""

    def to_sexpr(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class ImperativeFrame(SemanticFrame):
    """Imperative command frame."""

    action: str
    direct_object: EntityDescriptor | None = None
    relation: RelationFrame | None = None
    particles: tuple[str, ...] = ()

    def to_sexpr(self) -> str:
        """Serializes the imperative frame."""

        parts = ["command", self.action]
        if self.direct_object:
            parts.append(self.direct_object.to_sexpr())
        if self.relation:
            parts.append(self.relation.to_sexpr())
        for particle in self.particles:
            parts.append(f"(particle {particle})")
        return f"({' '.join(parts)})"


@dataclass(frozen=True)
class QueryFrame(SemanticFrame):
    """Question frame lowered from controlled English."""

    query_kind: str
    subject: EntityDescriptor | None = None
    relation: str | None = None
    object: EntityDescriptor | None = None
    wh: str | None = None
    modifiers: tuple[str, ...] = field(default_factory=tuple)

    def to_sexpr(self) -> str:
        """Serializes the query frame."""

        parts = ["query", self.query_kind]
        if self.wh:
            parts.append(f"(wh {self.wh})")
        if self.subject:
            parts.append(f"(subject {self.subject.to_sexpr()})")
        if self.relation:
            parts.append(f"(relation {self.relation})")
        if self.object:
            parts.append(f"(object {self.object.to_sexpr()})")
        for modifier in self.modifiers:
            parts.append(f"(modifier {modifier})")
        return f"({' '.join(parts)})"

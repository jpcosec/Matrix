"""Stable distinction between kernel symbols and Wi-level relations."""

from __future__ import annotations

from dataclasses import dataclass


KERNEL_CONNECTIVES = frozenset({"and", "or", "not", "if"})
KERNEL_META_RELATIONS = frozenset({"instance", "equivalent"})
WI_RELATION_FAMILIES = frozenset(
    {
        "has_property",
        "in_state",
        "event1",
        "event2",
        "event3",
        "part_of",
        "depends_on",
        "causes",
        "precedes",
    }
)


@dataclass(frozen=True)
class SymbolPolicy:
    """Describes where one candidate symbol belongs."""

    symbol: str
    layer: str
    role: str
    stability: str
    rationale: str


def classify_symbol(symbol: str) -> SymbolPolicy:
    """Classifies a candidate form as kernel-level or Wi-level."""

    if symbol in KERNEL_CONNECTIVES:
        return SymbolPolicy(
            symbol=symbol,
            layer="kernel",
            role="connective",
            stability="keep",
            rationale="logical composition belongs to the operational kernel, not to asserted domain facts",
        )
    if symbol in KERNEL_META_RELATIONS:
        rationale = {
            "instance": "typing and class membership are kernel-significant for database grounding, admissibility, and query planning",
            "equivalent": "canonicalization and alias folding are kernel-significant for symbol normalization across sources",
        }[symbol]
        return SymbolPolicy(
            symbol=symbol,
            layer="kernel",
            role="meta-relation",
            stability="keep",
            rationale=rationale,
        )
    if symbol in WI_RELATION_FAMILIES:
        stability = "defer" if symbol.startswith("event") else "keep"
        rationale = (
            "event arity helpers are surface-level relation families and should remain outside the kernel; they are likely temporary sugar rather than deep primitives"
            if symbol.startswith("event")
            else "this is domain knowledge that should be stored as asserted relational content inside Wi, not as reserved kernel code"
        )
        return SymbolPolicy(
            symbol=symbol,
            layer="wi",
            role="relation-family",
            stability=stability,
            rationale=rationale,
        )
    return SymbolPolicy(
        symbol=symbol,
        layer="unknown",
        role="unclassified",
        stability="defer",
        rationale="the symbol is not part of the first stable kernel policy",
    )


def is_kernel_symbol(symbol: str) -> bool:
    """Reports whether one symbol belongs to the kernel."""

    return classify_symbol(symbol).layer == "kernel"

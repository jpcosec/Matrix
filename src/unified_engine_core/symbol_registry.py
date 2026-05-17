"""Sign-to-symbol registry used by the unified engine."""

from __future__ import annotations


class SymbolRegistry:
    """Maps external signs to internal symbol identifiers."""

    def __init__(self) -> None:
        """Initializes the bidirectional sign and symbol registries."""

        self.symbol_to_signs: dict[str, set[str]] = {}
        self.sign_to_symbol: dict[str, str] = {}

    def register_symbol(self, symbol_id: str, initial_sign: str | None = None) -> None:
        """Registers a symbol and optionally binds an initial sign."""

        if symbol_id not in self.symbol_to_signs:
            self.symbol_to_signs[symbol_id] = set()
        if initial_sign:
            self.add_sign(symbol_id, initial_sign)

    def add_sign(self, symbol_id: str, sign: str) -> None:
        """Associates a sign with a symbol identifier."""

        if symbol_id not in self.symbol_to_signs:
            self.register_symbol(symbol_id)
        self.symbol_to_signs[symbol_id].add(sign)
        self.sign_to_symbol[sign] = symbol_id

    def get_symbol(self, sign: str) -> str | None:
        """Looks up the symbol identifier for a sign."""

        return self.sign_to_symbol.get(sign)

    def get_signs(self, symbol_id: str) -> list[str]:
        """Returns all registered signs for a symbol."""

        return list(self.symbol_to_signs.get(symbol_id, []))

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedPropositions:
    subject: str
    relation: str
    property: str
    modifier: Optional[str]
    raw: str
    confidence: float


class NaturalLanguageParser:
    PATTERNS = [
        (r"(.+?) tiene (.+?) (.+)", "has_property_with_modifier"),
        (r"(.+?) tiene (.+)", "has_property"),
        (r"(.+?) es un? (.+)", "is_type"),
        (r"(.+?) es (.+)", "is_property"),
        (r"buscar (.+) con (.+)", "query_with"),
        (r"buscar (.+)", "query"),
        (r"¿?(?:la |el |los |las )?(.+?) (?:tiene|tienen) (.+?)\??", "question_has"),
        (r"¿?(?:la |el |los |las )?(.+?) es (?:un|una) (.+?)\??", "question_is_type"),
    ]

    PROPERTY_NORMALIZATION = {
        "hoja": "hoja",
        "hojas": "hoja",
        "raíz": "raíz",
        "raices": "raíz",
        "tallo": "tallo",
        "tallos": "tallo",
        "color": "color",
        "verde": "verde",
        "rojo": "rojo",
        "flor": "flor",
        "comestible": "comestible",
        "rugosa": "hoja.rugosa",
        "lisa": "hoja.lisa",
        "rugoso": "hoja.rugosa",
        "liso": "hoja.lisa",
    }

    MODIFIER_MAP = {
        "rugosa": "hoja.rugosa",
        "rugoso": "hoja.rugosa",
        "lisa": "hoja.lisa",
        "liso": "hoja.lisa",
        "redonda": "forma.redonda",
        "ondulada": "forma.ondulada",
    }

    def __init__(self):
        self.compiled_patterns = [(re.compile(p, re.IGNORECASE), name) for p, name in self.PATTERNS]

    def parse(self, text: str) -> ParsedPropositions:
        text = text.strip()
        for pattern, name in self.compiled_patterns:
            match = pattern.match(text)
            if match:
                return self._handle_match(name, match, text)
        return self._parse_fallback(text)

    def _handle_match(self, pattern_name: str, match: re.Match, raw: str) -> ParsedPropositions:
        groups = match.groups()
        raw_cleaned = raw.replace("¿", "").replace("?", "").replace("¡", "").replace("!", "").strip()

        if pattern_name == "has_property":
            subject = self._normalize_subject(groups[0])
            prop = self._normalize_property(groups[1])
            return ParsedPropositions(
                subject=subject,
                relation="has_property",
                property=prop,
                modifier=None,
                raw=raw_cleaned,
                confidence=0.9
            )

        elif pattern_name == "has_property_with_modifier":
            subject = self._normalize_subject(groups[0])
            base_prop = self._normalize_property(groups[1])
            modifier = self._normalize_modifier(groups[2])
            full_prop = f"{base_prop}.{modifier}" if base_prop in self.MODIFIER_MAP else base_prop
            return ParsedPropositions(
                subject=subject,
                relation="has_property",
                property=full_prop,
                modifier=modifier,
                raw=raw_cleaned,
                confidence=0.85
            )

        elif pattern_name == "is_type":
            subject = self._normalize_subject(groups[0])
            type_name = self._normalize_property(groups[1])
            return ParsedPropositions(
                subject=subject,
                relation="is_type",
                property=type_name,
                modifier=None,
                raw=raw_cleaned,
                confidence=0.8
            )

        elif pattern_name == "query_with":
            entity = self._normalize_subject(groups[0])
            prop = self._normalize_property(groups[1])
            return ParsedPropositions(
                subject=entity,
                relation="query",
                property=prop,
                modifier=None,
                raw=raw_cleaned,
                confidence=0.9
            )

        elif pattern_name == "question_has":
            subject = self._normalize_subject(groups[0])
            prop = self._normalize_property(groups[1])
            return ParsedPropositions(
                subject=subject,
                relation="ask_property",
                property=prop,
                modifier=None,
                raw=raw_cleaned,
                confidence=0.9
            )

        elif pattern_name == "question_is_type":
            subject = self._normalize_subject(groups[0])
            type_name = self._normalize_property(groups[1])
            return ParsedPropositions(
                subject=subject,
                relation="is_type",
                property=type_name,
                modifier=None,
                raw=raw_cleaned,
                confidence=0.9
            )

        return self._parse_fallback(raw_cleaned)

    def _normalize_subject(self, text: str) -> str:
        text = text.strip().lower()
        text = text.replace("¿", "").replace("?", "").replace("¡", "").replace("!", "")
        normalizations = {
            "la lechuga": "lechuga",
            "el apio": "apio",
            "la espinaca": "espinaca",
            "la zanahoria": "zanahoria",
            "la coliflor": "coliflor",
            "el brócoli": "brócoli",
            "la papa": "papa",
            "el tomate": "tomate",
            "¿la lechuga": "lechuga",
            "¿el apio": "apio",
            "¿la espinaca": "espinaca",
            "¿la zanahoria": "zanahoria",
        }
        return normalizations.get(text, text)

    def _normalize_property(self, text: str) -> str:
        text = text.strip().lower()
        text = text.replace("?", "").replace("¿", "")
        return self.PROPERTY_NORMALIZATION.get(text, text)

    def _normalize_modifier(self, text: str) -> str:
        text = text.strip().lower()
        mod = self.MODIFIER_MAP.get(text)
        if mod:
            parts = mod.split(".")
            return parts[1] if len(parts) > 1 else mod
        return text

    def _parse_fallback(self, text: str) -> ParsedPropositions:
        words = text.lower().split()
        subject = words[0] if words else "unknown"
        prop = words[-1] if words else "unknown"
        return ParsedPropositions(
            subject=subject,
            relation="unknown",
            property=prop,
            modifier=None,
            raw=text,
            confidence=0.3
        )

    def parse_batch(self, texts: list[str]) -> list[ParsedPropositions]:
        return [self.parse(text) for text in texts]


class LogicalValidator:
    def __init__(self, engine):
        self.engine = engine

    def validate(self, proposition: ParsedPropositions) -> dict:
        if proposition.subject not in self.engine.ctx.objects:
            return {
                "valid": False,
                "reason": f"Unknown subject: {proposition.subject}",
                "suggestions": self._find_similar_objects(proposition.subject)
            }

        if proposition.property not in self.engine.ctx.properties:
            return {
                "valid": False,
                "reason": f"Unknown property: {proposition.property}",
                "suggestions": self._find_similar_properties(proposition.property)
            }

        if proposition.relation in ["has_property", "is_property", "ask_property"]:
            status = self.engine.get_status(proposition.subject, proposition.property)
            return {
                "valid": True,
                "proposition": proposition,
                "status": status,
                "type": self._classify_proposition(status, proposition)
            }

        return {
            "valid": True,
            "proposition": proposition,
            "status": {"status": "unknown", "truth": None, "truth_label": "N/A"},
            "type": "unhandled_relation"
        }

    def _classify_proposition(self, status: dict, prop: ParsedPropositions) -> str:
        if status["status"] == "unsinnig":
            return "unsinnig_contextual"
        if status["truth_label"] == "TRUE":
            return "sinnvoll_true"
        if status["truth_label"] == "FALSE":
            return "sinnvoll_false"
        if status["truth_label"] == "UNKNOWN":
            return "sinnlos_unknown"
        return "unknown"

    def _find_similar_objects(self, subject: str) -> list[str]:
        similar = []
        for obj in self.engine.ctx.objects:
            if subject in obj or obj in subject:
                similar.append(obj)
        return similar[:5]

    def _find_similar_properties(self, prop: str) -> list[str]:
        similar = []
        for p in self.engine.ctx.properties:
            if prop in p or p in prop:
                similar.append(p)
        return similar[:5]

    def process_query(self, proposition: ParsedPropositions) -> dict:
        if proposition.relation == "query":
            results = self.engine.query([proposition.property])
            return {
                "query": proposition.raw,
                "results": results
            }
        if proposition.relation == "ask_property":
            status = self.engine.get_status(proposition.subject, proposition.property)
            return {
                "question": proposition.raw,
                "subject": proposition.subject,
                "property": proposition.property,
                "answer": status
            }
        return {"error": "Cannot process this query type"}


def demo():
    print("=" * 70)
    print("NATURAL LANGUAGE PARSER DEMO")
    print("=" * 70)

    from multivalued_engine import MultiValuedMatrixEngine

    engine = MultiValuedMatrixEngine.load("examples/multivalued.yaml")
    parser = NaturalLanguageParser()
    validator = LogicalValidator(engine)

    test_sentences = [
        "La lechuga tiene hoja",
        "La espinaca tiene hoja rugosa",
        "¿La zanahoria tiene hoja?",
        "Buscar vegetales con comestible",
        "La coliflor tiene hoja rugosa",
        "Buscar hoja",
        "La papa es un vegetal",
        "El apio tiene tallo",
        "¿La lechuga tiene flor?",
        "La espinaca tiene hoja lisa",
    ]

    print(f"\n📝 Parsing {len(test_sentences)} sentences...\n")

    for sentence in test_sentences:
        prop = parser.parse(sentence)
        print(f"Input: \"{sentence}\"")
        print(f"  → Subject: {prop.subject}")
        print(f"  → Relation: {prop.relation}")
        print(f"  → Property: {prop.property}")
        print(f"  → Confidence: {prop.confidence}")

        validation = validator.validate(prop)
        if validation["valid"]:
            if "status" in validation:
                status_info = validation['status']
                truth_label = status_info.get('truth_label', status_info.get('status', 'N/A'))
                print(f"  → Status: {status_info.get('status', 'unknown')} ({truth_label})")
                print(f"  → Type: {validation['type']}")
        else:
            print(f"  → ERROR: {validation['reason']}")
            if validation.get("suggestions"):
                print(f"  → Suggestions: {validation['suggestions']}")
        print()


if __name__ == "__main__":
    demo()
"""Lowering from SHRDLU semantic frames to Matrix runtime operations."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.operational_model import LogicalSystem, OperationResult, SExpressionRuntime

from .dialog_state import DialogState
from .english_parser import parse_controlled_english
from .semantic_frames import EntityDescriptor, ImperativeFrame, QueryFrame, SemanticFrame


@dataclass(frozen=True)
class SceneObject:
    """Minimal prototype object descriptor."""

    symbol_id: str
    noun: str
    adjectives: tuple[str, ...] = ()


@dataclass
class PrototypeHarness:
    """Tiny end-to-end harness for the separate SHRDLU prototype."""

    system: LogicalSystem = field(default_factory=LogicalSystem)
    dialog: DialogState = field(default_factory=DialogState)
    scene_wigame_id: str = "wigame:scene"
    scene_objects: dict[str, SceneObject] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.runtime = SExpressionRuntime(self.system)
        if not self.scene_objects:
            self.scene_objects = {
                "red-block": SceneObject("red-block", "block", ("red",)),
                "blue-cube": SceneObject("blue-cube", "cube", ("blue",)),
                "green-pyramid": SceneObject("green-pyramid", "pyramid", ("green",)),
            }
        self._bootstrap_scene()

    def execute(self, sentence: str) -> OperationResult:
        """Parses, lowers, and executes one prototype sentence."""

        frame = parse_controlled_english(sentence)
        result = lower_frame(frame, self)
        if result.status == "accept" and result.payload and "referents" in result.payload:
            self.dialog.remember(*result.payload["referents"])
        return result

    def _bootstrap_scene(self) -> None:
        self.runtime.evaluate("(create relation on on)")
        for obj in self.scene_objects.values():
            self.runtime.evaluate(f"(create symbol {obj.symbol_id} {obj.symbol_id})")
        axis_a = " ".join(sorted(self.scene_objects))
        axis_b = axis_a
        self.runtime.evaluate(f"(create li li:scene on (axis-a {axis_a}) (axis-b {axis_b}))")
        self.runtime.evaluate(f"(create wigame {self.scene_wigame_id} li:scene)")


def lower_frame(frame: SemanticFrame, harness: PrototypeHarness) -> OperationResult:
    """Lowers a semantic frame into runtime operations and executes them."""

    if isinstance(frame, ImperativeFrame):
        return _lower_imperative(frame, harness)
    if isinstance(frame, QueryFrame):
        return _lower_query(frame, harness)
    raise ValueError(f"unsupported prototype frame: {type(frame).__name__}")


def _lower_imperative(frame: ImperativeFrame, harness: PrototypeHarness) -> OperationResult:
    if frame.action != "put" or frame.direct_object is None or frame.relation is None:
        return OperationResult(status="reject", reason="prototype only supports `put X on Y` commands for now")
    source = _resolve_entity(frame.direct_object, harness)
    if source.status != "accept":
        return source
    target = _resolve_entity(frame.relation.target, harness)
    if target.status != "accept":
        return target
    source_id = source.payload["referents"][0]
    target_id = target.payload["referents"][0]
    result = harness.runtime.evaluate(f"(assert {harness.scene_wigame_id} (on {source_id} {target_id}))")
    payload = dict(result.payload or {})
    payload["referents"] = [source_id]
    return OperationResult(status=result.status, sinn=result.sinn, payload=payload, reason=result.reason)


def _lower_query(frame: QueryFrame, harness: PrototypeHarness) -> OperationResult:
    if frame.query_kind != "truth" or frame.subject is None or frame.object is None or frame.relation != "on":
        return OperationResult(status="reject", reason="prototype only supports truth queries over `on` for now")
    subject = _resolve_entity(frame.subject, harness)
    if subject.status != "accept":
        return subject
    obj = _resolve_entity(frame.object, harness)
    if obj.status != "accept":
        return obj
    subject_id = subject.payload["referents"][0]
    object_id = obj.payload["referents"][0]
    result = harness.runtime.evaluate(f"(check {harness.scene_wigame_id} (on {subject_id} {object_id}))")
    payload = dict(result.payload or {})
    payload["referents"] = [subject_id]
    return OperationResult(status=result.status, sinn=result.sinn, payload=payload, reason=result.reason)


def _resolve_entity(entity: EntityDescriptor, harness: PrototypeHarness) -> OperationResult:
    if entity.referent:
        referents = harness.dialog.resolve_pronoun(entity.referent)
        if not referents:
            return OperationResult(status="ambiguous", reason="prototype referent is unresolved", payload={"referents": []})
        if len(referents) > 1:
            return OperationResult(status="ambiguous", reason="prototype referent has multiple candidates", payload={"referents": list(referents)})
        return OperationResult(status="accept", payload={"referents": list(referents)})

    noun = entity.noun
    adjectives = set(entity.adjectives)
    matches = [
        obj.symbol_id
        for obj in harness.scene_objects.values()
        if (noun is None or obj.noun == noun) and adjectives.issubset(set(obj.adjectives))
    ]
    if not matches:
        return OperationResult(status="reject", reason="prototype entity has no matching object", payload={"referents": []})
    if len(matches) > 1:
        return OperationResult(status="ambiguous", reason="prototype entity matches multiple objects", payload={"referents": matches})
    return OperationResult(status="accept", payload={"referents": matches})

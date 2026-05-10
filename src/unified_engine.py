from __future__ import annotations
import jax.numpy as jnp
import yaml
import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class TruthValue(IntEnum):
    T = 2
    F = 0
    U = 1
    N = -1

    def __str__(self):
        return {2: "T", 0: "F", 1: "U", -1: "N"}[self.value]

    @property
    def label(self):
        return {2: "TRUE", 0: "FALSE", 1: "UNKNOWN", -1: "NOT_APPLICABLE"}[self.value]


@dataclass
class Context:
    name: str
    objects: list[str]
    properties: list[str]
    objects_meta: dict
    properties_meta: dict
    truths: dict
    subcontexts: dict = field(default_factory=dict)


@dataclass
class Bridge:
    name: str
    from_context: str
    to_context: str
    from_objects: list[str]
    to_objects: list[str]
    relation: str = "has_relation"


@dataclass
class SubContext:
    name: str
    parent_property: str
    objects: list[str]
    properties: list[str]
    truths: dict


class UnifiedMatrixEngine:
    M_T = TruthValue.T
    M_F = TruthValue.F
    M_U = TruthValue.U
    M_N = TruthValue.N

    def __init__(self, contexts: dict[str, Context] = None, bridges: list[Bridge] = None, subcontexts: dict[str, SubContext] = None):
        self.contexts = contexts or {}
        self.bridges = bridges or []
        self.subcontexts = subcontexts or {}
        self.M: dict[str, jnp.ndarray] = {}
        self.S: dict[str, jnp.ndarray] = {}
        self._bridge_matrices: dict[str, jnp.ndarray] = {}
        self._build_all_matrices()

    def _build_all_matrices(self):
        for ctx_name, ctx in self.contexts.items():
            self.M[ctx_name] = self._build_M(ctx)
            self.S[ctx_name] = self._build_S(ctx, self.M[ctx_name])
        self._build_bridge_matrices()

    def _build_M(self, ctx: Context) -> jnp.ndarray:
        n, m = len(ctx.objects), len(ctx.properties)
        data = jnp.full((n, m), self.M_U.value, dtype=jnp.int8)
        for i, obj_name in enumerate(ctx.objects):
            for j, prop_name in enumerate(ctx.properties):
                value = ctx.truths.get(obj_name, {}).get(prop_name)
                if value is not None:
                    if isinstance(value, bool):
                        data = data.at[i, j].set(self.M_T.value if value else self.M_F.value)
                    elif isinstance(value, str):
                        tv = {"true": self.M_T, "false": self.M_F, "unknown": self.M_U, "na": self.M_N}.get(value.lower(), self.M_U)
                        data = data.at[i, j].set(tv.value)
        return data

    def _build_S(self, ctx: Context, M: jnp.ndarray) -> jnp.ndarray:
        n, m = len(ctx.objects), len(ctx.properties)
        S = jnp.ones((n, m), dtype=bool)
        for i, obj_name in enumerate(ctx.objects):
            obj_meta = ctx.objects_meta.get(obj_name, {})
            obj_class = obj_meta.get("class")
            for j, prop_name in enumerate(ctx.properties):
                prop_meta = ctx.properties_meta.get(prop_name, {})
                applies_to = prop_meta.get("applies_to")
                if applies_to and obj_class != applies_to:
                    S = S.at[i, j].set(False)
                requires = prop_meta.get("applies_if", {})
                if requires:
                    req_prop = requires.get("property")
                    req_value = requires.get("value")
                    if req_prop in ctx.properties:
                        req_j = ctx.properties.index(req_prop)
                        if M[i, req_j] != (self.M_T.value if req_value else self.M_F.value):
                            S = S.at[i, j].set(False)
        return S

    def _build_bridge_matrices(self):
        for bridge in self.bridges:
            from_ctx = self.contexts.get(bridge.from_context)
            to_ctx = self.contexts.get(bridge.to_context)
            if from_ctx and to_ctx:
                R = jnp.zeros((len(from_ctx.objects), len(to_ctx.objects)), dtype=bool)
                for fo in bridge.from_objects:
                    if fo in from_ctx.objects:
                        i = from_ctx.objects.index(fo)
                        if fo in bridge.from_objects:
                            idx = bridge.from_objects.index(fo)
                            if idx < len(bridge.to_objects):
                                to_obj = bridge.to_objects[idx]
                                if to_obj in to_ctx.objects:
                                    j = to_ctx.objects.index(to_obj)
                                    R = R.at[i, j].set(True)
                self._bridge_matrices[bridge.name] = R

    def _bool_mult(self, A: jnp.ndarray, B: jnp.ndarray) -> jnp.ndarray:
        return jnp.logical_or.reduce(
            jnp.logical_and(A[:, :, None], B[None, :, :]),
            axis=1
        )

    def get_status(self, obj: str, prop: str, context: str = None) -> dict:
        ctx_name = context or "vegetales"
        ctx = self.contexts.get(ctx_name)
        if not ctx:
            for ctx_name, ctx in self.contexts.items():
                if obj in ctx.objects and prop in ctx.properties:
                    break
            else:
                return {"error": "Object or property not found"}

        if obj not in ctx.objects or prop not in ctx.properties:
            return {"error": f"Object or property not found"}

        i = ctx.objects.index(obj)
        j = ctx.properties.index(prop)
        applicable = bool(self.S[ctx_name][i, j])
        truth = TruthValue(int(self.M[ctx_name][i, j]))

        if not applicable:
            return {"status": "unsinnig", "truth": str(truth), "truth_label": "NOT_APPLICABLE", "applicable": False}

        return {
            "status": "sinnvoll",
            "truth": str(truth),
            "truth_label": truth.label,
            "applicable": True
        }

    def query(self, properties: list[str], context: str = None) -> list[str]:
        ctx_name = context
        ctx = self.contexts.get(ctx_name) if ctx_name else None
        if not ctx:
            for ctx_name, ctx in self.contexts.items():
                all_props_exist = all(p in ctx.properties for p in properties)
                if all_props_exist:
                    break
            else:
                return []

        results = []
        for i, obj in enumerate(ctx.objects):
            if all(self.M[ctx_name][i, ctx.properties.index(p)] == self.M_T.value for p in properties if p in ctx.properties):
                results.append(obj)
        return results

    def compose(self, ctx1: str, ctx2: str, via_bridge: str = None) -> jnp.ndarray:
        if via_bridge and via_bridge in self._bridge_matrices:
            return self._bridge_matrices[via_bridge]
        M1 = self.M.get(ctx1)
        M2 = self.M.get(ctx2)
        if M1 is not None and M2 is not None:
            return self._bool_mult(M1, M2.T)
        return jnp.array([])

    def route_to_subcontext(self, obj: str, prop: str) -> dict:
        sub = self.subcontexts.get(prop)
        if sub:
            i = sub.objects.index(obj) if obj in sub.objects else -1
            if i >= 0:
                sub_M = self._build_M(sub)
                return {
                    "object": obj,
                    "subcontext": sub.name,
                    "properties": {sub.properties[j]: bool(sub_M[i, j]) for j in range(len(sub.properties))}
                }
        return {"error": f"No subcontext for {prop}"}

    def classify_all(self, context: str = None) -> dict:
        ctx_name = context or list(self.contexts.keys())[0]
        ctx = self.contexts.get(ctx_name)
        if not ctx:
            return {}

        result = {"sinnvoll_true": [], "sinnvoll_false": [], "sinnlos_unknown": [], "unsinnig": []}
        for i, obj in enumerate(ctx.objects):
            for j, prop in enumerate(ctx.properties):
                applicable = bool(self.S[ctx_name][i, j])
                truth = TruthValue(int(self.M[ctx_name][i, j]))
                pair = (obj, prop)

                if not applicable:
                    result["unsinnig"].append(pair)
                elif truth == TruthValue.T:
                    result["sinnvoll_true"].append(pair)
                elif truth == TruthValue.F:
                    result["sinnvoll_false"].append(pair)
                else:
                    result["sinnlos_unknown"].append(pair)
        return result

    @staticmethod
    def load(path: str) -> UnifiedMatrixEngine:
        with open(path) as f:
            data = yaml.safe_load(f)

        contexts = {}
        for ctx_name, ctx_data in data.get("contexts", {}).items():
            contexts[ctx_name] = Context(
                name=ctx_name,
                objects=list(ctx_data.get("objects", {}).keys()),
                properties=list(ctx_data.get("properties", {}).keys()),
                objects_meta=ctx_data.get("objects", {}),
                properties_meta=ctx_data.get("properties", {}),
                truths=ctx_data.get("truths", {})
            )

        bridges = []
        for bridge_data in data.get("bridges", []):
            bridges.append(Bridge(
                name=bridge_data.get("name", "bridge"),
                from_context=bridge_data.get("from", ""),
                to_context=bridge_data.get("to", ""),
                from_objects=bridge_data.get("from_objects", []),
                to_objects=bridge_data.get("to_objects", []),
                relation=bridge_data.get("relation", "has_relation")
            ))

        subcontexts = {}
        for prop_name, sub_data in data.get("subcontexts", {}).items():
            subcontexts[prop_name] = SubContext(
                name=sub_data.get("name", f"{prop_name}_sub"),
                parent_property=prop_name,
                objects=sub_data.get("objects", []),
                properties=sub_data.get("properties", []),
                truths=sub_data.get("truths", {})
            )

        return UnifiedMatrixEngine(contexts, bridges, subcontexts)


class NLParser:
    PROPERTY_MAP = {
        "hoja": "hoja", "hojas": "hoja",
        "raíz": "raíz", "raices": "raíz",
        "tallo": "tallo", "tallos": "tallo",
        "flor": "flor", "comestible": "comestible",
        "rugosa": "hoja.rugosa", "rugoso": "hoja.rugosa",
        "lisa": "hoja.lisa", "liso": "hoja.lisa",
        "verde": "verde", "rojo": "rojo",
    }

    def parse(self, text: str) -> dict:
        text = text.strip().replace("¿", "").replace("?", "").replace("¡", "").replace("!", "").strip().lower()

        subject_match = re.match(r"(?:la |el |los |las )?(\w+)", text)
        subject = subject_match.group(1) if subject_match else "unknown"

        for pattern, replacement in self.PROPERTY_MAP.items():
            if pattern in text.lower():
                return {
                    "subject": subject,
                    "property": replacement,
                    "raw": text,
                    "relation": "has_property"
                }

        return {"subject": subject, "property": "unknown", "raw": text, "relation": "unknown"}


def demo():
    print("=" * 70)
    print("UNIFIED MATRIX ENGINE DEMO")
    print("=" * 70)

    with open("examples/unified.yaml", "w") as f:
        yaml.dump({
            "contexts": {
                "vegetales": {
                    "objects": {
                        "lechuga": {"class": "vegetal"},
                        "espinaca": {"class": "vegetal"},
                        "zanahoria": {"class": "vegetal"},
                        "apio": {"class": "vegetal"}
                    },
                    "properties": {
                        "hoja": {"applies_to": "vegetal"},
                        "raíz": {"applies_to": "vegetal"},
                        "tallo": {"applies_to": "vegetal"},
                        "comestible": {"applies_to": "vegetal"},
                        "hoja.rugosa": {"applies_if": {"property": "hoja", "value": True}},
                        "hoja.lisa": {"applies_if": {"property": "hoja", "value": True}}
                    },
                    "truths": {
                        "lechuga": {"hoja": True, "raíz": False, "tallo": False, "comestible": True, "hoja.rugosa": False, "hoja.lisa": True},
                        "espinaca": {"hoja": True, "raíz": False, "tallo": False, "comestible": True, "hoja.rugosa": True, "hoja.lisa": False},
                        "zanahoria": {"hoja": False, "raíz": True, "tallo": False, "comestible": True},
                        "apio": {"hoja": False, "raíz": False, "tallo": True, "comestible": True}
                    }
                },
                "colores": {
                    "objects": {
                        "verde": {"class": "color"},
                        "rojo": {"class": "color"}
                    },
                    "properties": {
                        "color": {"applies_to": "color"}
                    },
                    "truths": {
                        "verde": {"color": True},
                        "rojo": {"color": True}
                    }
                }
            },
            "bridges": [
                {
                    "name": "vegetal_color",
                    "from": "vegetales",
                    "to": "colores",
                    "from_objects": ["lechuga", "espinaca", "zanahoria", "apio"],
                    "to_objects": ["verde", "verde", "rojo", "verde"]
                }
            ],
            "subcontexts": {
                "hoja": {
                    "name": "hojas_sub",
                    "objects": ["lechuga", "espinaca", "zanahoria", "apio"],
                    "properties": ["rugosa", "lisa", "forma"],
                    "truths": {
                        "lechuga": {"rugosa": False, "lisa": True, "forma": "redonda"},
                        "espinaca": {"rugosa": True, "lisa": False, "forma": "ondulada"}
                    }
                }
            }
        }, f, allow_unicode=True)

    engine = UnifiedMatrixEngine.load("examples/unified.yaml")

    print(f"\n📦 Contexts: {list(engine.contexts.keys())}")
    print(f"🌉 Bridges: {[b.name for b in engine.bridges]}")
    print(f"🔀 Subcontexts: {list(engine.subcontexts.keys())}")

    print("\n" + "=" * 70)
    print("QUERY EXAMPLES")
    print("=" * 70)

    print(f"\n🔍 Query [hoja, hoja.lisa]: {engine.query(['hoja', 'hoja.lisa'])}")
    print(f"🔍 Query [tallo]: {engine.query(['tallo'])}")
    print(f"🔍 Query [comestible]: {engine.query(['comestible'])}")

    print("\n" + "=" * 70)
    print("STATUS CHECKS")
    print("=" * 70)

    tests = [
        ("lechuga", "hoja"),
        ("lechuga", "hoja.rugosa"),
        ("zanahoria", "hoja.rugosa"),
        ("espinaca", "comestible"),
    ]
    for obj, prop in tests:
        status = engine.get_status(obj, prop)
        print(f"  {obj} + {prop}: {status}")

    print("\n" + "=" * 70)
    print("CONTEXT COMPOSITION")
    print("=" * 70)

    C = engine.compose("vegetales", "colores", "vegetal_color")
    print(f"\nBridge matrix shape: {C.shape}")
    print("vegetal → color:")
    ctx = engine.contexts["vegetales"]
    for i, obj in enumerate(ctx.objects):
        print(f"  {obj}: {C[i].astype(int)}")

    print("\n" + "=" * 70)
    print("SUBCONTEXT ROUTING")
    print("=" * 70)

    for obj in ["lechuga", "espinaca"]:
        result = engine.route_to_subcontext(obj, "hoja")
        print(f"\n  {obj} + hoja:")
        print(f"    {result}")

    print("\n" + "=" * 70)
    print("CLASSIFICATION")
    print("=" * 70)

    classified = engine.classify_all()
    for category, items in classified.items():
        print(f"\n  {category}: {len(items)} entries")
        for item in items[:3]:
            print(f"    {item}")


if __name__ == "__main__":
    demo()
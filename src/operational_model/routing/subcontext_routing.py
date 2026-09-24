from __future__ import annotations
import jax.numpy as jnp
import yaml
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SubContext:
    name: str
    parent_property: str
    objects: list[str]
    properties: list[str]
    truths: dict[str, dict]
    objects_meta: dict = field(default_factory=dict)
    properties_meta: dict = field(default_factory=dict)

    def get_M(self) -> jnp.ndarray:
        n, m = len(self.objects), len(self.properties)
        M = jnp.zeros((n, m), dtype=bool)
        for obj_name, obj_props in self.truths.items():
            if obj_name in self.objects:
                i = self.objects.index(obj_name)
                for prop_name, value in obj_props.items():
                    if prop_name in self.properties:
                        j = self.properties.index(prop_name)
                        M = M.at[i, j].set(bool(value))
        return M

    def get_S(self) -> jnp.ndarray:
        n, m = len(self.objects), len(self.properties)
        S = jnp.ones((n, m), dtype=bool)
        return S


@dataclass
class SubcontextRouter:
    name: str
    parent_context: str
    subcontexts: dict[str, SubContext]
    routing_rules: dict[str, str]

    def route(self, obj: str, prop: str) -> Optional[SubContext]:
        key = f"{obj}|{prop}"
        if key in self.routing_rules:
            return self.subcontexts.get(self.routing_rules[key])
        if prop in self.subcontexts:
            return self.subcontexts.get(prop)
        return None

    def route_to_subcontext(self, prop: str) -> Optional[SubContext]:
        return self.subcontexts.get(prop)

    def get_all_routes(self) -> dict:
        return {
            "subcontexts": list(self.subcontexts.keys()),
            "routing_rules": self.routing_rules
        }


class HierarchicalMatrixEngine:
    def __init__(self, context_name: str):
        self.context_name = context_name
        self.objects: list[str] = []
        self.properties: list[str] = []
        self.truths: dict[str, dict] = {}
        self.objects_meta: dict = {}
        self.properties_meta: dict = {}
        self.M: jnp.ndarray = None
        self.S: jnp.ndarray = None
        self.subcontexts: dict[str, SubContext] = {}
        self.routers: list[SubcontextRouter] = []

    def add_property(self, prop: str, meta: dict = None):
        if prop not in self.properties:
            self.properties.append(prop)
            self.properties_meta[prop] = meta or {}

    def add_object(self, obj: str, facts: dict[str, bool], meta: dict = None):
        if obj not in self.objects:
            self.objects.append(obj)
            self.truths[obj] = {}
        self.truths[obj].update(facts)
        self.objects_meta[obj] = meta or {}

        for prop, value in facts.items():
            if prop not in self.properties:
                self.add_property(prop)

    def create_subcontext(self, parent_prop: str, sub_name: str, properties: list[str], facts: dict[str, dict] = None):
        sub = SubContext(
            name=sub_name,
            parent_property=parent_prop,
            objects=self.objects.copy(),
            properties=properties,
            truths=facts or {}
        )
        self.subcontexts[parent_prop] = sub

        router = SubcontextRouter(
            name=f"router_{parent_prop}",
            parent_context=self.context_name,
            subcontexts={sub_name: sub},
            routing_rules={parent_prop: sub_name}
        )
        self.routers.append(router)
        return sub

    def build_matrices(self):
        n, m = len(self.objects), len(self.properties)
        self.M = jnp.zeros((n, m), dtype=bool)
        self.S = jnp.ones((n, m), dtype=bool)

        for i, obj in enumerate(self.objects):
            for j, prop in enumerate(self.properties):
                value = self.truths.get(obj, {}).get(prop)
                if value is not None:
                    self.M = self.M.at[i, j].set(bool(value))
                else:
                    self.M = self.M.at[i, j].set(False)

                prop_meta = self.properties_meta.get(prop, {})
                requires = prop_meta.get("applies_if", {})
                if requires:
                    req_prop = requires.get("property")
                    req_value = requires.get("value")
                    if req_prop in self.properties:
                        req_j = self.properties.index(req_prop)
                        if self.M[i, req_j] != bool(req_value):
                            self.S = self.S.at[i, j].set(False)

    def query(self, properties: list[str], mode: str = "conjunctive") -> list[str]:
        if mode == "conjunctive":
            pattern = jnp.zeros(len(self.properties), dtype=bool)
            for p in properties:
                if p in self.properties:
                    j = self.properties.index(p)
                    pattern = pattern.at[j].set(True)
            matches = jnp.all(self.M == pattern, axis=1)
            return [self.objects[i] for i in range(len(self.objects)) if matches[i]]

        elif mode == "disjunctive":
            pattern = jnp.zeros(len(self.properties), dtype=bool)
            for p in properties:
                if p in self.properties:
                    j = self.properties.index(p)
                    pattern = pattern.at[j].set(True)
            matches = jnp.any(self.M == pattern, axis=1) | jnp.any(self.M, axis=1)
            return [self.objects[i] for i in range(len(self.objects)) if matches[i]]

        return []

    def query_routed(self, obj: str, prop: str) -> dict:
        sub = self.subcontexts.get(prop)
        if sub:
            i = sub.objects.index(obj) if obj in sub.objects else -1
            results = {}
            if i >= 0:
                sub_M = sub.get_M()
                for j, sub_prop in enumerate(sub.properties):
                    results[sub_prop] = bool(sub_M[i, j])
            return {
                "object": obj,
                "parent_property": sub.parent_property,
                "subcontext": sub.name,
                "subproperties": results
            }
        return {"error": f"No subcontext for property {prop}"}

    def get_property_cooccurrence(self) -> jnp.ndarray:
        return self._bool_mult(self.M.T, self.M)

    def get_object_similarity(self) -> jnp.ndarray:
        return self._bool_mult(self.M, self.M.T)

    def _bool_mult(self, A: jnp.ndarray, B: jnp.ndarray) -> jnp.ndarray:
        return jnp.logical_or.reduce(
            jnp.logical_and(A[:, :, None], B[None, :, :]),
            axis=1
        )

    @staticmethod
    def load(path: str) -> HierarchicalMatrixEngine:
        with open(path) as f:
            data = yaml.safe_load(f)

        engine = HierarchicalMatrixEngine(data["context"])

        for obj, meta in data.get("objects", {}).items():
            engine.objects.append(obj)
            engine.objects_meta[obj] = meta

        for prop, meta in data.get("properties", {}).items():
            engine.add_property(prop, meta)

        for obj, facts in data.get("truths", {}).items():
            engine.truths[obj] = facts

        subcontexts_data = data.get("subcontexts", {})
        for parent_prop, sub_data in subcontexts_data.items():
            sub = SubContext(
                name=sub_data.get("name", f"{parent_prop}_sub"),
                parent_property=parent_prop,
                objects=engine.objects,
                properties=sub_data.get("properties", []),
                truths=sub_data.get("truths", {})
            )
            engine.subcontexts[parent_prop] = sub

            engine.routers.append(SubcontextRouter(
                name=f"router_{parent_prop}",
                parent_context=engine.context_name,
                subcontexts={parent_prop: sub},
                routing_rules={parent_prop: parent_prop}
            ))

        engine.build_matrices()
        return engine

    def to_dict(self) -> dict:
        return {
            "context": self.context_name,
            "objects": self.objects,
            "properties": self.properties,
            "M": self.M.tolist() if self.M is not None else None,
            "subcontexts": {
                name: {
                    "properties": sub.properties,
                    "truths": sub.truths
                }
                for name, sub in self.subcontexts.items()
            }
        }


def demo():
    print("=" * 70)
    print("SUBCONTEXT ROUTING DEMO")
    print("=" * 70)

    with open("examples/vegetales_hierarchical.yaml", "w") as f:
        yaml.dump({
            "context": "vegetales",
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
                "hoja.rugosa": {"applies_if": {"property": "hoja", "value": True}},
                "hoja.lisa": {"applies_if": {"property": "hoja", "value": True}}
            },
            "truths": {
                "lechuga": {"hoja": True, "raíz": False, "tallo": False, "hoja.lisa": True},
                "espinaca": {"hoja": True, "raíz": False, "tallo": False, "hoja.rugosa": True},
                "zanahoria": {"hoja": False, "raíz": True, "tallo": False},
                "apio": {"hoja": False, "raíz": False, "tallo": True}
            },
            "subcontexts": {
                "hoja": {
                    "name": "hojas_subcontext",
                    "properties": ["rugosa", "lisa", "forma"],
                    "truths": {
                        "lechuga": {"rugosa": False, "lisa": True, "forma": "redonda"},
                        "espinaca": {"rugosa": True, "lisa": False, "forma": "ondulada"}
                    }
                }
            }
        }, f)

    engine = HierarchicalMatrixEngine.load("examples/vegetales_hierarchical.yaml")

    print(f"\n📦 Context: {engine.context_name}")
    print(f"Objects: {engine.objects}")
    print(f"Properties: {engine.properties}")
    print(f"Subcontexts: {list(engine.subcontexts.keys())}")

    print("\n" + "=" * 70)
    print("MATRIX M (truth)")
    print("=" * 70)
    print(f"Shape: {engine.M.shape}")
    print(engine.M.astype(int))

    print("\n" + "=" * 70)
    print("SUBCONTEXT: hojas")
    print("=" * 70)

    sub = engine.subcontexts.get("hoja")
    if sub:
        print(f"Name: {sub.name}")
        print(f"Parent property: {sub.parent_property}")
        print(f"Properties: {sub.properties}")
        print(f"Truths:")
        sub_M = sub.get_M()
        print(f"  M shape: {sub_M.shape}")
        for i, obj in enumerate(sub.objects):
            print(f"    {obj}: {dict(zip(sub.properties, sub_M[i].astype(int).tolist()))}")

    print("\n" + "=" * 70)
    print("ROUTING QUERIES")
    print("=" * 70)

    print(f"\nQuery 'hoja' → routes to subcontext:")
    print(f" lechuga: {engine.query_routed('lechuga', 'hoja')}")
    print(f" espinaca: {engine.query_routed('espinaca', 'hoja')}")

    print("\n" + "=" * 70)
    print("CONJUNCTIVE vs DISJUNCTIVE QUERIES")
    print("=" * 70)

    print(f"\nQuery [hoja, hoja.lisa] (AND):")
    print(f"  Conjunctive: {engine.query(['hoja', 'hoja.lisa'], 'conjunctive')}")
    print(f"  Disjunctive: {engine.query(['hoja', 'hoja.lisa'], 'disjunctive')}")

    print(f"\nQuery [tallo]:")
    print(f"  Result: {engine.query(['tallo'])}")

    print("\n" + "=" * 70)
    print("PROPERTY CO-OCCURRENCE (M^T ⊗ M)")
    print("=" * 70)

    cooc = engine.get_property_cooccurrence()
    print(f"Shape: {cooc.shape}")
    print("Properties:", engine.properties)
    print(cooc.astype(int))

    print("\n" + "=" * 70)
    print("OBJECT SIMILARITY (M ⊗ M^T)")
    print("=" * 70)

    sim = engine.get_object_similarity()
    print(f"Shape: {sim.shape}")
    print("Objects:", engine.objects)
    print(sim.astype(int))


if __name__ == "__main__":
    demo()
from __future__ import annotations
import jax.numpy as jnp
import jax
from jax import jit
import yaml
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Context:
    name: str
    objects: list[str]
    properties: list[str]
    objects_meta: dict
    properties_meta: dict
    truths: dict


@dataclass
class Bridge:
    name: str
    from_context: str
    to_context: str
    relation_type: str
    from_objects: list[str]
    to_objects: list[str]

    def as_matrix(self, from_n: int, to_n: int) -> jnp.ndarray:
        R = jnp.zeros((from_n, to_n), dtype=bool)
        for i, fo in enumerate(self.from_objects):
            if fo in self.from_objects and self.to_objects:
                try:
                    j = self.to_objects.index(self.to_objects[i] if i < len(self.to_objects) else self.to_objects[0])
                    R = R.at[i, j].set(True)
                except:
                    pass
        return R


class ComposableMatrixEngine:
    def __init__(self, context: Context):
        self.ctx = context
        self.M = self._build_M()
        self.S = self._build_S()

    def _build_M(self) -> jnp.ndarray:
        n, m = len(self.ctx.objects), len(self.ctx.properties)
        data = jnp.zeros((n, m), dtype=bool)
        for obj_name, obj_props in self.ctx.truths.items():
            if obj_name in self.ctx.objects:
                i = self.ctx.objects.index(obj_name)
                for prop_name, value in obj_props.items():
                    if prop_name in self.ctx.properties:
                        j = self.ctx.properties.index(prop_name)
                        data = data.at[i, j].set(bool(value))
        return data

    def _build_S(self) -> jnp.ndarray:
        n, m = len(self.ctx.objects), len(self.ctx.properties)
        data = jnp.ones((n, m), dtype=bool)
        for i, obj_name in enumerate(self.ctx.objects):
            obj_meta = self.ctx.objects_meta.get(obj_name, {})
            obj_class = obj_meta.get("class")
            for j, prop_name in enumerate(self.ctx.properties):
                prop_meta = self.ctx.properties_meta.get(prop_name, {})
                applies_to = prop_meta.get("applies_to")
                if applies_to and obj_class != applies_to:
                    data = data.at[i, j].set(False)
                    continue
                requires = prop_meta.get("applies_if", {})
                if requires:
                    req_prop = requires.get("property")
                    req_value = requires.get("value")
                    if req_prop and req_prop in self.ctx.properties:
                        req_j = self.ctx.properties.index(req_prop)
                        if self.M[i, req_j] != bool(req_value):
                            data = data.at[i, j].set(False)
        return data

    def M_T(self) -> jnp.ndarray:
        return self.M.T

    def _bool_mult(self, A: jnp.ndarray, B: jnp.ndarray) -> jnp.ndarray:
        return jnp.logical_or.reduce(
            jnp.logical_and(A[:, :, None], B[None, :, :]),
            axis=1
        )

    def mult(self, other: jnp.ndarray = None, direction: str = "standard") -> jnp.ndarray:
        if direction == "M^T ⊗ M":
            A = self.M.T
            B = self.M
        elif direction == "M ⊗ M^T":
            A = self.M
            B = self.M.T
        elif other is not None:
            A = self.M
            B = other
        else:
            A = self.M
            B = self.M
        return self._bool_mult(A, B)

    def property_cooccurrence(self) -> jnp.ndarray:
        return self._bool_mult(self.M.T, self.M)

    def object_similarity(self) -> jnp.ndarray:
        return self._bool_mult(self.M, self.M.T)

    def query(self, properties: list[str]) -> list[str]:
        pattern = jnp.zeros(len(self.ctx.properties), dtype=bool)
        for p in properties:
            if p in self.ctx.properties:
                j = self.ctx.properties.index(p)
                pattern = pattern.at[j].set(True)
        results = jnp.all(self.M == pattern, axis=1)
        return [self.ctx.objects[i] for i in range(len(self.ctx.objects)) if results[i]]

    def semantic_status(self, obj: str, prop: str) -> dict:
        i = self.ctx.objects.index(obj)
        j = self.ctx.properties.index(prop)
        applicable = bool(self.S[i, j])
        truth = bool(self.M[i, j])
        has_explicit_entry = prop in self.ctx.truths.get(obj, {})

        if not applicable:
            return {"status": "unsinnig_contextual", "applicable": False, "truth": truth}
        if not has_explicit_entry:
            return {"status": "sinnlos_not_covered", "applicable": True, "truth": truth}
        return {"status": "sinnvoll", "applicable": applicable, "truth": truth}

    @staticmethod
    def load(path: str) -> ComposableMatrixEngine:
        with open(path) as f:
            data = yaml.safe_load(f)
        ctx = Context(
            name=data["context"],
            objects=list(data["objects"].keys()),
            properties=list(data["properties"].keys()),
            objects_meta=data["objects"],
            properties_meta=data["properties"],
            truths=data["truths"]
        )
        return ComposableMatrixEngine(ctx)


class ComposedContext:
    def __init__(self, engines: dict[str, ComposableMatrixEngine], bridges: list[Bridge] = None):
        self.engines = engines
        self.bridges = bridges or []
        self._bridge_matrices = {}
        self._build_bridge_matrices()

    def _build_bridge_matrices(self):
        for bridge in self.bridges:
            from_eng = self.engines.get(bridge.from_context)
            to_eng = self.engines.get(bridge.to_context)
            if from_eng and to_eng:
                R = jnp.zeros((len(from_eng.ctx.objects), len(to_eng.ctx.objects)), dtype=bool)
                for fo in bridge.from_objects:
                    if fo in from_eng.ctx.objects:
                        i = from_eng.ctx.objects.index(fo)
                        to_obj = bridge.to_objects[bridge.from_objects.index(fo)] if fo in bridge.from_objects and bridge.from_objects.index(fo) < len(bridge.to_objects) else None
                        if to_obj and to_obj in to_eng.ctx.objects:
                            j = to_eng.ctx.objects.index(to_obj)
                            R = R.at[i, j].set(True)
                self._bridge_matrices[bridge.name] = R

    def compose(self, ctx1_name: str, ctx2_name: str, via_bridge: str = None) -> jnp.ndarray:
        eng1 = self.engines.get(ctx1_name)
        eng2 = self.engines.get(ctx2_name)

        if not eng1 or not eng2:
            raise ValueError(f"Contexts not found")

        if via_bridge and via_bridge in self._bridge_matrices:
            R = self._bridge_matrices[via_bridge]
            result = jnp.zeros((len(eng1.ctx.objects), len(eng2.ctx.objects)), dtype=bool)
            for i in range(R.shape[0]):
                if i < len(eng1.ctx.objects):
                    for j in range(R.shape[1]):
                        if j < len(eng2.ctx.objects) and R[i, j]:
                            result = result.at[i, j].set(True)
            return result

        return self._bool_mult(eng1.M, eng2.M)

    def _bool_mult(self, A: jnp.ndarray, B: jnp.ndarray) -> jnp.ndarray:
        return jnp.logical_or.reduce(
            jnp.logical_and(A[:, :, None], B[None, :, :]),
            axis=1
        )

    def _bool_mult_path(self, M1: jnp.ndarray, props1: list, R: jnp.ndarray, props2: list) -> jnp.ndarray:
        return self._bool_mult(R, R.T)

    def route_query(self, start_ctx: str, properties: list[str], through_bridges: list[str] = None) -> dict:
        current_engine = self.engines.get(start_ctx)
        if not current_engine:
            return {"error": f"Context {start_ctx} not found"}

        results = current_engine.query(properties)

        if through_bridges:
            for bridge_name in through_bridges:
                if bridge_name not in self._bridge_matrices:
                    continue
                R = self._bridge_matrices[bridge_name]
                bridge = next((b for b in self.bridges if b.name == bridge_name), None)
                if not bridge:
                    continue

                next_engine = self.engines.get(bridge.to_context)
                if not next_engine:
                    continue

                routed_results = []
                for obj in results:
                    if obj in current_engine.ctx.objects:
                        i = current_engine.ctx.objects.index(obj)
                        for j in range(len(next_engine.ctx.objects)):
                            if R[i, j]:
                                routed_results.append(next_engine.ctx.objects[j])
                results = list(set(routed_results))

        return {
            "context": start_ctx,
            "results": results,
            "through": through_bridges or []
        }

    def check_composability(self, ctx1_name: str, ctx2_name: str) -> dict:
        eng1 = self.engines.get(ctx1_name)
        eng2 = self.engines.get(ctx2_name)
        if not eng1 or not eng2:
            return {"composable": False, "reason": "context not found"}

        compatible_bridges = []
        for bridge in self.bridges:
            if bridge.from_context == ctx1_name and bridge.to_context == ctx2_name:
                compatible_bridges.append(bridge.name)

        if not compatible_bridges:
            return {
                "composable": False,
                "reason": f"No bridge from {ctx1_name} to {ctx2_name}"
            }

        return {
            "composable": True,
            "bridges": compatible_bridges,
            "from_objects": eng1.ctx.objects,
            "to_objects": eng2.ctx.objects
        }


def demo():
    print("=" * 70)
    print("CONTEXT COMPOSITION DEMO")
    print("=" * 70)

    print("\n📁 Loading contexts...")
    engine_v = ComposableMatrixEngine.load("examples/vegetales.yaml")
    print(f"✓ Loaded: {engine_v.ctx.name} | objects: {engine_v.ctx.objects}")

    with open("examples/colores.yaml", "w") as f:
        yaml.dump({
            "context": "colores",
            "objects": {
                "verde": {"class": "color"},
                "rojo": {"class": "color"},
                "amarillo": {"class": "color"}
            },
            "properties": {
                "color": {"applies_to": "color"}
            },
            "truths": {
                "verde": {"color": True},
                "rojo": {"color": True},
                "amarillo": {"color": True}
            }
        }, f)

    engine_c = ComposableMatrixEngine.load("examples/colores.yaml")
    print(f"✓ Loaded: {engine_c.ctx.name} | objects: {engine_c.ctx.objects}")

    print("\n" + "=" * 70)
    print("BRIDGE DEFINITION")
    print("=" * 70)

    bridge = Bridge(
        name="vegetal_tiene_color",
        from_context="vegetales",
        to_context="colores",
        relation_type="tiene_color",
        from_objects=["lechuga", "espinaca", "zanahoria", "apio", "tomate", "brócoli"],
        to_objects=["verde", "verde", "rojo", "verde", "rojo", "verde"]
    )
    print(f"✓ Bridge: {bridge.name}")
    print(f"  {bridge.from_context} → {bridge.to_context}")
    print(f"  Mappings: {list(zip(bridge.from_objects, bridge.to_objects))}")

    print("\n" + "=" * 70)
    print("COMPOSABILITY CHECK")
    print("=" * 70)

    composed = ComposedContext(
        engines={"vegetales": engine_v, "colores": engine_c},
        bridges=[bridge]
    )

    check = composed.check_composability("vegetales", "colores")
    print(f"vegetales ↔ colores: {check}")

    print("\n" + "=" * 70)
    print("BRIDGE MATRIX R (vegetales → colores)")
    print("=" * 70)

    R = composed._bridge_matrices.get("vegetal_tiene_color")
    if R is not None:
        print(f"Shape: {R.shape}")
        print("    verde  rojo  amar")
        for i, obj in enumerate(engine_v.ctx.objects):
            print(f"  {obj:8} {R[i].astype(int)}")

    print("\n" + "=" * 70)
    print("COMPOSITION: W_vegetales ⊗ R ⊗ W_colores")
    print("=" * 70)

    C = composed.compose("vegetales", "colores", "vegetal_tiene_color")
    print(f"Composed matrix shape: {C.shape}")
    print("\n  vegetal → color association via bridge:")
    print("    verde  rojo  amar")
    for i, obj in enumerate(engine_v.ctx.objects):
        print(f"  {obj:8} {C[i].astype(int)}")

    print("\n" + "=" * 70)
    print("ROUTING QUERIES")
    print("=" * 70)

    result1 = composed.route_query("vegetales", ["hoja", "hoja.rugosa"], ["vegetal_tiene_color"])
    print(f"\nQuery 'hoja.rugosa' in vegetales, route to colores:")
    print(f"  Raw results: {engine_v.query(['hoja.rugosa'])}")
    print(f"  Routed to colores: {result1}")

    result2 = composed.route_query("vegetales", ["tallo"])
    print(f"\nQuery 'tallo' (no routing):")
    print(f"  Results: {result2}")

    print("\n" + "=" * 70)
    print("M^T ⊗ M (property co-occurrence within vegetales)")
    print("=" * 70)

    cooc = engine_v.property_cooccurrence()
    print("Properties:", engine_v.ctx.properties)
    print(cooc.astype(int))

    print("\n" + "=" * 70)
    print("M ⊗ M^T (object similarity within vegetales)")
    print("=" * 70)

    sim = engine_v.object_similarity()
    print("Objects:", engine_v.ctx.objects)
    print(sim.astype(int))


if __name__ == "__main__":
    demo()
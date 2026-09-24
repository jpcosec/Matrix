from __future__ import annotations
import jax.numpy as jnp
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, Tuple
import yaml


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
class MultiValuedContext:
    name: str
    objects: list[str]
    properties: list[str]
    objects_meta: dict
    properties_meta: dict
    truths: dict


class MultiValuedMatrixEngine:
    M_T = TruthValue.T
    M_F = TruthValue.F
    M_U = TruthValue.U
    M_N = TruthValue.N

    def __init__(self, context: MultiValuedContext):
        self.ctx = context
        self.M = self._build_M()
        self.S = self._build_S()

    def _build_M(self) -> jnp.ndarray:
        n, m = len(self.ctx.objects), len(self.ctx.properties)
        data = jnp.full((n, m), self.M_U.value, dtype=jnp.int8)
        for i, obj_name in enumerate(self.ctx.objects):
            for j, prop_name in enumerate(self.ctx.properties):
                value = self.ctx.truths.get(obj_name, {}).get(prop_name)
                if value is not None:
                    if isinstance(value, bool):
                        data = data.at[i, j].set(self.M_T.value if value else self.M_F.value)
                    elif isinstance(value, str):
                        tv = {"true": self.M_T, "false": self.M_F, "unknown": self.M_U, "na": self.M_N}.get(value.lower(), self.M_U)
                        data = data.at[i, j].set(tv.value)
        return data

    def _build_S(self) -> jnp.ndarray:
        n, m = len(self.ctx.objects), len(self.ctx.properties)
        S = jnp.ones((n, m), dtype=bool)

        for i, obj_name in enumerate(self.ctx.objects):
            obj_meta = self.ctx.objects_meta.get(obj_name, {})
            obj_class = obj_meta.get("class")
            for j, prop_name in enumerate(self.ctx.properties):
                prop_meta = self.ctx.properties_meta.get(prop_name, {})
                applies_to = prop_meta.get("applies_to")
                if applies_to and obj_class != applies_to:
                    S = S.at[i, j].set(False)

                requires = prop_meta.get("applies_if", {})
                if requires:
                    req_prop = requires.get("property")
                    req_value = requires.get("value")
                    if req_prop in self.ctx.properties:
                        req_j = self.ctx.properties.index(req_prop)
                        if self.M[i, req_j] != (self.M_T.value if req_value else self.M_F.value):
                            S = S.at[i, j].set(False)
        return S

    def _bool_mult(self, A: jnp.ndarray, B: jnp.ndarray) -> jnp.ndarray:
        return jnp.logical_or.reduce(
            jnp.logical_and(A[:, :, None], B[None, :, :]),
            axis=1
        )

    def get_status(self, obj: str, prop: str) -> dict:
        i = self.ctx.objects.index(obj)
        j = self.ctx.properties.index(prop)
        applicable = bool(self.S[i, j])
        truth = TruthValue(self.M[i, j])

        if not applicable:
            return {
                "status": "unsinnig",
                "truth": str(truth),
                "truth_label": truth.label,
                "applicable": False
            }

        if truth == TruthValue.U:
            return {
                "status": "unknown",
                "truth": str(truth),
                "truth_label": truth.label,
                "applicable": True
            }

        if truth == TruthValue.T:
            return {
                "status": "sinnvoll",
                "truth": str(truth),
                "truth_label": truth.label,
                "applicable": True
            }

        return {
            "status": "sinnvoll_false",
            "truth": str(truth),
            "truth_label": truth.label,
            "applicable": True
        }

    def query(self, properties: list[str], require_all: bool = True) -> list[dict]:
        results = []
        for i, obj in enumerate(self.ctx.objects):
            match = True
            for p in properties:
                if p in self.ctx.properties:
                    j = self.ctx.properties.index(p)
                    if require_all:
                        if self.M[i, j] != self.M_T.value:
                            match = False
                            break
                    else:
                        if self.M[i, j] != self.M_T.value:
                            match = False
            if match:
                results.append({
                    "object": obj,
                    "properties": {p: str(TruthValue(self.M[i, self.ctx.properties.index(p)])) for p in properties if p in self.ctx.properties}
                })
        return results

    def query_with_sense(self, properties: list[str]) -> dict:
        applicable_objs = []
        true_objs = []
        false_objs = []
        unknown_objs = []

        for i, obj in enumerate(self.ctx.objects):
            all_applicable = all(self.S[i, self.ctx.properties.index(p)] for p in properties if p in self.ctx.properties)
            if all_applicable:
                applicable_objs.append(obj)
            all_true = all(self.M[i, self.ctx.properties.index(p)] == self.M_T.value for p in properties if p in self.ctx.properties)
            if all_true:
                true_objs.append(obj)
            any_false = any(self.M[i, self.ctx.properties.index(p)] == self.M_F.value for p in properties if p in self.ctx.properties)
            if any_false and all_applicable:
                false_objs.append(obj)
            any_unknown = any(self.M[i, self.ctx.properties.index(p)] == self.M_U.value for p in properties if p in self.ctx.properties)
            if any_unknown and all_applicable:
                unknown_objs.append(obj)

        return {
            "applicable": applicable_objs,
            "true": true_objs,
            "false_but_applicable": false_objs,
            "unknown": unknown_objs
        }

    def property_cooccurrence(self) -> jnp.ndarray:
        return self._bool_mult(self.M.astype(bool), self.M.astype(bool).T)

    def object_similarity(self) -> jnp.ndarray:
        return self._bool_mult(self.M.astype(bool), self.M.astype(bool).T)

    def get_value(self, obj: str, prop: str) -> TruthValue:
        i = self.ctx.objects.index(obj)
        j = self.ctx.properties.index(prop)
        return TruthValue(self.M[i, j])

    def set_value(self, obj: str, prop: str, value: TruthValue):
        i = self.ctx.objects.index(obj)
        j = self.ctx.properties.index(prop)
        self.M = self.M.at[i, j].set(value.value)

        requires = self.ctx.properties_meta.get(prop, {}).get("applies_if", {})
        if requires:
            req_prop = requires.get("property")
            if req_prop in self.ctx.properties:
                req_j = self.ctx.properties.index(req_prop)
                for k in range(self.M.shape[0]):
                    if self.M[k, j] == self.M_T.value and self.M[k, req_j] != (self.M_T.value if requires.get("value") else self.M_F.value):
                        self.M = self.M.at[k, j].set(self.M_F.value)
                        self.S = self.S.at[k, j].set(False)

    @staticmethod
    def load(path: str) -> MultiValuedMatrixEngine:
        with open(path) as f:
            data = yaml.safe_load(f)
        ctx = MultiValuedContext(
            name=data["context"],
            objects=list(data["objects"].keys()),
            properties=list(data["properties"].keys()),
            objects_meta=data["objects"],
            properties_meta=data["properties"],
            truths=data["truths"]
        )
        return MultiValuedMatrixEngine(ctx)


def demo():
    print("=" * 70)
    print("MULTI-VALUED LOGIC (T/F/U/N) DEMO")
    print("=" * 70)

    with open("examples/multivalued.yaml", "w") as f:
        yaml.dump({
            "context": "vegetales_mv",
            "objects": {
                "lechuga": {"class": "vegetal"},
                "espinaca": {"class": "vegetal"},
                "zanahoria": {"class": "vegetal"},
                "coliflor": {"class": "vegetal"},
                "papa": {"class": "vegetal"}
            },
            "properties": {
                "hoja": {"applies_to": "vegetal"},
                "raíz": {"applies_to": "vegetal"},
                "flor": {"applies_to": "vegetal"},
                "comestible": {"applies_to": "vegetal"},
                "hoja.rugosa": {"applies_if": {"property": "hoja", "value": True}}
            },
            "truths": {
                "lechuga": {"hoja": "true", "raíz": "false", "flor": "unknown", "comestible": "true", "hoja.rugosa": "false"},
                "espinaca": {"hoja": "true", "raíz": "false", "flor": "false", "comestible": "true", "hoja.rugosa": "true"},
                "zanahoria": {"hoja": "false", "raíz": "true", "flor": "false", "comestible": "true", "hoja.rugosa": "na"},
                "coliflor": {"hoja": "true", "raíz": "true", "flor": "true", "comestible": "true", "hoja.rugosa": "unknown"},
                "papa": {"hoja": "false", "raíz": "true", "flor": "false", "comestible": "true"}
            }
        }, f)

    engine = MultiValuedMatrixEngine.load("examples/multivalued.yaml")

    print(f"\n📦 Context: {engine.ctx.name}")
    print(f"Objects: {engine.ctx.objects}")
    print(f"Properties: {engine.ctx.properties}")

    print("\n" + "=" * 70)
    print("MULTI-VALUED MATRIX M")
    print("=" * 70)
    print("Legend: T=TRUE, F=FALSE, U=UNKNOWN, N=NOT_APPLICABLE")
    print("\n         ", "  ".join(f"{p[:8]:>8}" for p in engine.ctx.properties))
    for i, obj in enumerate(engine.ctx.objects):
        row = [str(TruthValue(v)) for v in engine.M[i].tolist()]
        print(f"  {obj:8} ", "  ".join(f"{v:>8}" for v in row))

    print("\n" + "=" * 70)
    print("S MATRIX (applicable)")
    print("=" * 70)
    print("         ", "  ".join(f"{p[:8]:>8}" for p in engine.ctx.properties))
    for i, obj in enumerate(engine.ctx.objects):
        print(f"  {obj:8} ", "  ".join(f"{int(v):>8}" for v in engine.S[i].tolist()))

    print("\n" + "=" * 70)
    print("SEMANTIC STATUS")
    print("=" * 70)
    test_cases = [
        ("lechuga", "hoja"),
        ("lechuga", "flor"),
        ("zanahoria", "hoja.rugosa"),
        ("espinaca", "hoja.rugosa"),
        ("coliflor", "hoja.rugosa"),
        ("zanahoria", "comestible"),
    ]
    for obj, prop in test_cases:
        status = engine.get_status(obj, prop)
        print(f"  {obj} + {prop}: {status['status']} ({status['truth_label']})")

    print("\n" + "=" * 70)
    print("QUERY RESULTS")
    print("=" * 70)
    print(f"\nQuery [comestible=true] (require all):")
    results = engine.query(["comestible"])
    for r in results:
        print(f"  {r}")

    print(f"\nQuery [hoja, hoja.rugosa] with sense:")
    sense = engine.query_with_sense(["hoja.rugosa"])
    print(f"  true: {sense['true']}")
    print(f"  unknown: {sense['unknown']}")
    print(f"  false_but_applicable: {sense['false_but_applicable']}")

    print("\n" + "=" * 70)
    print("TRUTH VALUE OPERATIONS")
    print("=" * 70)
    print(f"\nTruth values available:")
    for tv in [TruthValue.T, TruthValue.F, TruthValue.U, TruthValue.N]:
        print(f"  {tv} = {tv.label}")

    print(f"\nSample status checks:")
    print(f"  lechuga+hoja = {engine.get_status('lechuga', 'hoja')['truth_label']}")
    print(f"  lechuga+flor = {engine.get_status('lechuga', 'flor')['truth_label']}")
    print(f" zanahoria+hoja.rugosa = {engine.get_status('zanahoria', 'hoja.rugosa')['truth_label']}")


if __name__ == "__main__":
    demo()
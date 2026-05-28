from __future__ import annotations
import jax.numpy as jnp
import jax
from jax import jit
import yaml
from dataclasses import dataclass
from typing import Optional


@dataclass
class Context:
    name: str
    objects: list[str]
    properties: list[str]
    objects_meta: dict
    properties_meta: dict
    truths: dict

    def object_index(self, obj: str) -> int:
        return self.objects.index(obj)

    def property_index(self, prop: str) -> int:
        return self.properties.index(prop)


class BooleanMatrixEngine:
    def __init__(self, context: Context):
        self.ctx = context
        self.M = self._build_M()
        self.S = self._build_S()
        self._compile_operations()

    def _build_M(self) -> jnp.ndarray:
        n, m = len(self.ctx.objects), len(self.ctx.properties)
        data = jnp.zeros((n, m), dtype=bool)
        for obj_name, obj_props in self.ctx.truths.items():
            i = self.ctx.object_index(obj_name)
            for prop_name, value in obj_props.items():
                if prop_name in self.ctx.properties:
                    j = self.ctx.property_index(prop_name)
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
                            continue

                if prop_meta.get("requires_property"):
                    req_prop = prop_meta["requires_property"]
                    if req_prop in self.ctx.properties:
                        req_j = self.ctx.properties.index(req_prop)
                        if not self.M[i, req_j]:
                            data = data.at[i, j].set(False)

        return data

    def _compile_operations(self):
        @jit
        def boolean_matrix_mult(A, B):
            return jnp.logical_or.reduce(
                jnp.logical_and(A[:, :, None], B[None, :, :]),
                axis=1
            )

        @jit
        def query_conjunctive(M, property_indices):
            pattern = jnp.zeros_like(M[0], dtype=bool).at[property_indices].set(True)
            return jnp.all(M == pattern, axis=1)

        self._boolean_mult = boolean_matrix_mult
        self._query_conj = query_conjunctive

    def M_T(self) -> jnp.ndarray:
        return self.M.T

    def mult(self, other: jnp.ndarray, direction: str = "standard") -> jnp.ndarray:
        if direction == "M^T ⊗ M":
            return self._boolean_mult(self.M.T, self.M)
        elif direction == "M ⊗ M^T":
            return self._boolean_mult(self.M, self.M.T)
        return self._boolean_mult(self.M, other)

    def property_cooccurrence(self) -> jnp.ndarray:
        return self.mult(self.M, "M^T ⊗ M")

    def object_similarity(self) -> jnp.ndarray:
        return self.mult(self.M, "M ⊗ M^T")

    def query(self, properties: list[str]) -> list[str]:
        indices = [self.ctx.property_index(p) for p in properties]
        results = self._query_conj(self.M, jnp.array(indices))
        return [self.ctx.objects[i] for i in range(len(self.ctx.objects)) if results[i]]

    def query_with_sense(self, properties: list[str]) -> dict:
        indices = [self.ctx.property_index(p) for p in properties]
        sense_indices = jnp.array([self.ctx.property_index(p) for p in properties])

        applicable = jnp.all(self.S[:, sense_indices], axis=1)
        satisfied = jnp.all(self.M[:, sense_indices], axis=1)
        both = jnp.logical_and(applicable, satisfied)

        return {
            "applicable": [self.ctx.objects[i] for i in range(len(self.ctx.objects)) if applicable[i]],
            "true": [self.ctx.objects[i] for i in range(len(self.ctx.objects)) if both[i]],
            "false_but_applicable": [self.ctx.objects[i] for i in range(len(self.ctx.objects)) if jnp.logical_and(applicable[i], ~satisfied[i])],
            "not_applicable": [self.ctx.objects[i] for i in range(len(self.ctx.objects)) if ~applicable[i]]
        }

    def detect_tautologies(self) -> list[str]:
        all_true = jnp.all(self.M, axis=0)
        return [self.ctx.properties[j] for j in range(len(self.ctx.properties)) if all_true[j]]

    def detect_contradictions(self) -> list[str]:
        all_false = jnp.all(~self.M, axis=0)
        return [self.ctx.properties[j] for j in range(len(self.ctx.properties)) if all_false[j]]

    def detect_ambiguous(self) -> dict:
        return {
            self.ctx.objects[i]: self.ctx.objects[j]
            for i in range(len(self.ctx.objects))
            for j in range(i + 1, len(self.ctx.objects))
            if jnp.array_equal(self.M[i], self.M[j])
        }

    def semantic_status(self, obj: str, prop: str) -> dict:
        i = self.ctx.object_index(obj)
        j = self.ctx.property_index(prop)
        applicable = bool(self.S[i, j])
        truth = bool(self.M[i, j])
        has_explicit_entry = prop in self.ctx.truths.get(obj, {})

        if not applicable:
            return {
                "status": "unsinnig_contextual",
                "applicable": False,
                "truth": truth,
                "has_explicit_entry": has_explicit_entry,
                "reason": "property not applicable in this context"
            }
        if not has_explicit_entry:
            return {
                "status": "sinnlos_not_covered",
                "applicable": True,
                "truth": truth,
                "has_explicit_entry": False,
                "reason": "applicable but not logically covered (no explicit entry)"
            }
        if truth:
            return {
                "status": "sinnvoll",
                "applicable": True,
                "truth": True,
                "has_explicit_entry": True,
                "reason": "proposition is applicable and true"
            }
        return {
            "status": "sinnvoll",
            "applicable": True,
            "truth": False,
            "has_explicit_entry": True,
            "reason": "proposition is applicable but false"
        }

    def classify_all(self) -> dict:
        classification = {
            "sinnvoll_true": [],
            "sinnvoll_false": [],
            "sinnlos_not_covered": [],
            "unsinnig_contextual": []
        }
        for i, obj in enumerate(self.ctx.objects):
            for j, prop in enumerate(self.ctx.properties):
                status = self.semantic_status(obj, prop)
                key = status["status"]
                if key == "sinnvoll" and status["truth"]:
                    classification["sinnvoll_true"].append((obj, prop))
                elif key == "sinnvoll" and not status["truth"]:
                    classification["sinnvoll_false"].append((obj, prop))
                else:
                    classification[key].append((obj, prop))
        return classification

    def S_meaning(self) -> jnp.ndarray:
        return self.S

    def S_covered(self) -> jnp.ndarray:
        covered = jnp.zeros((len(self.ctx.objects), len(self.ctx.properties)), dtype=bool)
        for i, obj in enumerate(self.ctx.objects):
            for j, prop in enumerate(self.ctx.properties):
                if prop in self.ctx.truths.get(obj, {}):
                    covered = covered.at[i, j].set(True)
        return covered

    def S_both(self) -> dict:
        S_meaning = self.S_meaning()
        S_cov = self.S_covered()
        S_meaning_only = jnp.logical_and(S_meaning, ~S_cov)
        S_covered_only = jnp.logical_and(S_cov, ~S_meaning)
        S_both = jnp.logical_and(S_meaning, S_cov)
        S_neither = jnp.logical_and(~S_meaning, ~S_cov)
        return {
            "meaning_and_covered": S_both.astype(int),
            "meaning_only": S_meaning_only.astype(int),
            "covered_only": S_covered_only.astype(int),
            "neither": S_neither.astype(int)
        }

    def compose_contexts(self, other: BooleanMatrixEngine) -> jnp.ndarray:
        return self.mult(other.M, "M ⊗ M^T")

    def insert_fact(self, obj: str, prop: str, value: bool):
        if obj not in self.ctx.objects:
            self.ctx.objects.append(obj)
            self.M = jnp.concatenate([self.M, jnp.zeros((1, self.M.shape[1]), dtype=bool)], axis=0)
            self.S = jnp.concatenate([self.S, jnp.ones((1, self.S.shape[1]), dtype=bool)], axis=0)

        if prop not in self.ctx.properties:
            self.ctx.properties.append(prop)
            self.M = jnp.concatenate([self.M, jnp.zeros((self.M.shape[0], 1), dtype=bool)], axis=1)
            self.S = jnp.concatenate([self.S, jnp.ones((self.S.shape[0], 1), dtype=bool)], axis=1)

        i = self.ctx.object_index(obj)
        j = self.ctx.property_index(prop)
        self.M = self.M.at[i, j].set(value)
        self._recompute_applicability(i, j, prop)

    def _recompute_applicability(self, obj_idx: int, prop_idx: int, prop_name: str):
        for j, other_prop in enumerate(self.ctx.properties):
            other_meta = self.ctx.properties_meta.get(other_prop, {})
            requires = other_meta.get("applies_if", {})
            if requires:
                req_prop = requires.get("property")
                req_value = requires.get("value")
                if req_prop == prop_name and req_prop in self.ctx.properties:
                    current_value = self.M[obj_idx, prop_idx]
                    if current_value != bool(req_value):
                        self.S = self.S.at[obj_idx, j].set(False)
                    else:
                        self.S = self.S.at[obj_idx, j].set(True)

    def insert_object(self, obj: str, facts: dict[str, bool]):
        if obj in self.ctx.objects:
            raise ValueError(f"Object {obj} already exists")
        self.ctx.objects.append(obj)
        self.ctx.objects_meta[obj] = {"class": "vegetal"}
        new_row_M = jnp.zeros(len(self.ctx.properties), dtype=bool)
        new_row_S = jnp.ones(len(self.ctx.properties), dtype=bool)
        i = len(self.ctx.objects) - 1
        for prop, value in facts.items():
            if prop not in self.ctx.properties:
                self.ctx.properties.append(prop)
                self.ctx.properties_meta[prop] = {}
                self.M = jnp.concatenate([self.M, jnp.zeros((self.M.shape[0], 1), dtype=bool)], axis=1)
                self.S = jnp.concatenate([self.S, jnp.ones((self.S.shape[0], 1), dtype=bool)], axis=1)
            j = self.ctx.property_index(prop)
            new_row_M = new_row_M.at[j].set(value)
            new_row_S = new_row_S.at[j].set(self._check_applicability_single(obj, prop, value))
        self.M = jnp.concatenate([self.M, new_row_M[None, :]], axis=0)
        self.S = jnp.concatenate([self.S, new_row_S[None, :]], axis=0)

    def _check_applicability_single(self, obj: str, prop: str, value: bool) -> bool:
        obj_meta = self.ctx.objects_meta.get(obj, {})
        prop_meta = self.ctx.properties_meta.get(prop, {})
        applies_to = prop_meta.get("applies_to")
        if applies_to and obj_meta.get("class") != applies_to:
            return False
        requires = prop_meta.get("applies_if", {})
        if requires:
            req_prop = requires.get("property")
            req_value = requires.get("value")
            if req_prop in self.ctx.properties:
                i = self.ctx.object_index(obj)
                req_j = self.ctx.property_index(req_prop)
                current_value = self.M[i, req_j]
                if current_value != bool(req_value):
                    return False
        return True

    @staticmethod
    def load(path: str) -> BooleanMatrixEngine:
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
        return BooleanMatrixEngine(ctx)


def demo():
    engine = BooleanMatrixEngine.load("examples/vegetales.yaml")

    print("=" * 60)
    print(f"Context: {engine.ctx.name}")
    print(f"Objects: {engine.ctx.objects}")
    print(f"Properties: {engine.ctx.properties}")
    print("=" * 60)

    print("\n📊 Matrix M (truth) - Initial:")
    print(engine.M.astype(int))

    print("\n" + "=" * 60)
    print("🔧 TEST 1: Insert new fact 'tomate tiene hoja.rugosa = true'")
    engine.insert_fact("tomate", "hoja.rugosa", True)
    print(f"New M shape: {engine.M.shape}")
    print(f"New property index: {engine.ctx.properties.index('hoja.rugosa')}")
    i = engine.ctx.object_index("tomate")
    j = engine.ctx.property_index("hoja.rugosa")
    print(f"  M[tomate, hoja.rugosa] = {int(engine.M[i, j])}")
    print(f"  S[tomate, hoja.rugosa] = {int(engine.S[i, j])} (should be 1 if tomate has hoja)")
    print(f"\n  🔍 Query [hoja.rugosa]: {engine.query(['hoja.rugosa'])}")

    print("\n" + "=" * 60)
    print("🔧 TEST 2: Insert 'tomate tiene hoja = true' then check applicability")
    engine.insert_fact("tomate", "hoja", True)
    print(f"  M[tomate, hoja] = {int(engine.M[engine.ctx.object_index('tomate'), engine.ctx.property_index('hoja')])}")
    print(f"  S[tomate, hoja.rugosa] = {int(engine.S[engine.ctx.object_index('tomate'), engine.ctx.property_index('hoja.rugosa')])} (should be 1 now)")
    print(f"\n  Status 'tomate has hoja.rugosa': {engine.semantic_status('tomate', 'hoja.rugosa')}")

    print("\n" + "=" * 60)
    print("🔧 TEST 3: Insert new object 'brócoli'")
    engine.insert_object("brócoli", {"hoja": True, "hoja.rugosa": False, "tallo": True})
    i = engine.ctx.object_index("brócoli")
    print(f"  New M[{i}] = {engine.M[i].astype(int)}")
    print(f"  S[{i}] = {engine.S[i].astype(int)}")
    print(f"\n  Query [hoja]: {engine.query(['hoja'])}")
    print(f"  Query [tallo]: {engine.query(['tallo'])}")

    print("\n" + "=" * 60)
    print("📋 S decomposition: meaning vs covered")
    S_decomp = engine.S_both()
    print("\nS_meaning (applicable in context):")
    print(S_decomp["meaning_and_covered"] + S_decomp["meaning_only"])
    print("\nS_covered (has explicit entry):")
    print(S_decomp["meaning_and_covered"] + S_decomp["covered_only"])
    print("\nS breakdown:")
    print(f"  meaning_and_covered (sinnvoll):\n{S_decomp['meaning_and_covered']}")
    print(f"  meaning_only (sinnlos - not covered):\n{S_decomp['meaning_only']}")
    print(f"  covered_only (inconsistent):\n{S_decomp['covered_only']}")
    print(f"  neither (unsinnig):\n{S_decomp['neither']}")

    print("\n" + "=" * 60)
    print("📋 Full classification:")
    classified = engine.classify_all()
    for cat, items in classified.items():
        print(f"\n{cat}: {items}")

    print("\n" + "=" * 60)
    print("📊 Final Matrix M:")
    print(engine.M.astype(int))
    print("\n📊 Final Matrix S:")
    print(engine.S.astype(int))

    print("\n🔗 Property co-occurrence (M^T ⊗ M):")
    print(engine.property_cooccurrence().astype(int))

    print("\n🔗 Object similarity (M ⊗ M^T):")
    print(engine.object_similarity().astype(int))


if __name__ == "__main__":
    demo()

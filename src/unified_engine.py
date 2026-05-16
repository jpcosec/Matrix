from __future__ import annotations
import jax.numpy as jnp
import jax
from jax import jit
import yaml
import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, Union


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


@dataclass
class Bridge:
    name: str
    from_context: str
    to_context: str
    from_objects: list[str]
    to_objects: list[str]
    relation: str = "has_relation"


class UnifiedMatrixEngine:
    """
    TKM MEEL (Máquina de Estados de Evaluación Lógica).
    A high-integrity engine for curated knowledge graphs using truth/sense segregation.
    """
    M_T = TruthValue.T
    M_F = TruthValue.F
    M_U = TruthValue.U
    M_N = TruthValue.N

    def __init__(self, contexts: dict[str, Context] = None, bridges: list[Bridge] = None):
        self.contexts = contexts or {}
        self.bridges = bridges or []
        
        # 4 Structural Masks per Context (TKM Atom: Mascaras_Estructurales)
        self.Vi: dict[str, jnp.ndarray] = {}  # Truth Matrix (Factual)
        self.Si: dict[str, jnp.ndarray] = {}  # Sense Mask (Applicability)
        self.Oi: dict[str, jnp.ndarray] = {}  # Observed Mask (Explicitly seen)
        self.Di: dict[str, jnp.ndarray] = {}  # Discriminative Mask (Reducción Descriptiva)
        
        self._bridge_matrices: dict[str, jnp.ndarray] = {}
        self._build_all_matrices()

    def _build_all_matrices(self):
        for ctx_name, ctx in self.contexts.items():
            self.Vi[ctx_name] = self._build_Vi(ctx)
            # Build Si depends on Vi for conditional applicability
            self.Si[ctx_name] = self._build_Si(ctx, self.Vi[ctx_name])
            self.Oi[ctx_name] = self._build_Oi(ctx)
            self.Di[ctx_name] = self._build_Di(ctx, self.Vi[ctx_name])
            
        self._build_bridge_matrices()

    def _build_Vi(self, ctx: Context) -> jnp.ndarray:
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

    def _build_Si(self, ctx: Context, Vi: jnp.ndarray) -> jnp.ndarray:
        n, m = len(ctx.objects), len(ctx.properties)
        S = jnp.ones((n, m), dtype=bool)
        for i, obj_name in enumerate(ctx.objects):
            obj_meta = ctx.objects_meta.get(obj_name, {})
            obj_class = obj_meta.get("class")
            for j, prop_name in enumerate(ctx.properties):
                prop_meta = ctx.properties_meta.get(prop_name, {})
                
                # Class restriction
                applies_to = prop_meta.get("applies_to")
                if applies_to and obj_class != applies_to:
                    S = S.at[i, j].set(False)
                    continue

                # Applicability dependency
                requires = prop_meta.get("applies_if", {})
                if requires:
                    req_prop = requires.get("property")
                    req_value = requires.get("value")
                    req_context = requires.get("context")

                    if req_context and req_context in self.contexts:
                        # Cross-context check
                        other_status = self.get_status(obj_name, req_prop, context=req_context)
                        if other_status.get("truth_label") != ("TRUE" if req_value else "FALSE"):
                            S = S.at[i, j].set(False)
                    elif req_prop in ctx.properties:
                        # Local check
                        req_j = ctx.properties.index(req_prop)
                        if Vi[i, req_j] != (self.M_T.value if req_value else self.M_F.value):
                            S = S.at[i, j].set(False)
        return S

    def _build_Oi(self, ctx: Context) -> jnp.ndarray:
        n, m = len(ctx.objects), len(ctx.properties)
        O = jnp.zeros((n, m), dtype=bool)
        for i, obj_name in enumerate(ctx.objects):
            for j, prop_name in enumerate(ctx.properties):
                if prop_name in ctx.truths.get(obj_name, {}):
                    O = O.at[i, j].set(True)
        return O

    def _build_Di(self, ctx: Context, Vi: jnp.ndarray) -> jnp.ndarray:
        # Reducción Descriptiva: detect tautologies/contradictions
        n, m = len(ctx.objects), len(ctx.properties)
        D = jnp.ones((n, m), dtype=bool)
        for j in range(m):
            col = Vi[:, j]
            # If property is true for ALL or false for ALL, it doesn't discriminate
            if jnp.all(col == self.M_T.value) or jnp.all(col == self.M_F.value):
                D = D.at[:, j].set(False)
        return D

    def _build_bridge_matrices(self):
        for bridge in self.bridges:
            from_ctx = self.contexts.get(bridge.from_context)
            to_ctx = self.contexts.get(bridge.to_context)
            if from_ctx and to_ctx:
                R = jnp.zeros((len(from_ctx.objects), len(to_ctx.objects)), dtype=bool)
                for fo in bridge.from_objects:
                    if fo in from_ctx.objects:
                        i = from_ctx.objects.index(fo)
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
        ctx_name = context
        if not ctx_name:
            for name, ctx in self.contexts.items():
                if obj in ctx.objects and prop in ctx.properties:
                    ctx_name = name
                    break
            else:
                return {
                    "status": "unsinnig", 
                    "reason": f"Coordinate ({obj}, {prop}) not found",
                    "truth": str(self.M_N), "truth_label": self.M_N.label, "applicable": False
                }

        ctx = self.contexts[ctx_name]
        if obj not in ctx.objects or prop not in ctx.properties:
            return {
                "status": "unsinnig", 
                "reason": f"Coordinate ({obj}, {prop}) missing in {ctx_name}",
                "truth": str(self.M_N), "truth_label": self.M_N.label, "applicable": False
            }

        i, j = ctx.objects.index(obj), ctx.properties.index(prop)
        applicable = bool(self.Si[ctx_name][i, j])
        truth = TruthValue(int(self.Vi[ctx_name][i, j]))
        observed = bool(self.Oi[ctx_name][i, j])
        discriminative = bool(self.Di[ctx_name][i, j])

        if not applicable:
            return {
                "status": "unsinnig", "truth": str(truth), "truth_label": "NOT_APPLICABLE", 
                "applicable": False, "reason": "Sense violation (Si=0)"
            }

        status = "sinnvoll" if discriminative else "sinnlos"
        return {
            "status": status, "truth": str(truth), "truth_label": truth.label,
            "applicable": True, "observed": observed, "discriminative": discriminative
        }

    def get_status_hierarchical(self, obj: str, relation: str, property: str) -> dict:
        # TKM Enrutamiento Jerárquico
        current_ctx = list(self.contexts.keys())[0]
        path = [current_ctx]
        while True:
            found = False
            for bridge in self.bridges:
                if bridge.from_context == current_ctx:
                    if obj in self.contexts[bridge.to_context].objects:
                        current_ctx = bridge.to_context
                        path.append(current_ctx)
                        found = True
                        break
            if not found: break
        
        target = f"{relation}.{property}"
        if target not in self.contexts[current_ctx].properties:
            target = property
            
        res = self.get_status(obj, target, context=current_ctx)
        res["path"] = path
        return res

    def get_information_energy(self, context: str) -> float:
        # TKM Energía de Información E(R)
        Vi, Si, Oi, Di = self.Vi[context], self.Si[context], self.Oi[context], self.Di[context]
        c = jnp.sum(Si).astype(float) / Si.size
        i = jnp.sum(jnp.logical_and(Vi == self.M_T.value, Si)).astype(float) / Vi.size
        o = jnp.sum(Oi).astype(float) / Oi.size
        d = jnp.sum(Di).astype(float) / Di.size
        return 0.25*(c + i + o + d)

    def run_dfa_reasoning(self, context: str, steps: int = 3) -> jnp.ndarray:
        # TKM Maquina de Estados DFA: operate on the square Similarity Matrix (Object-Object)
        V = (self.Vi[context] == self.M_T.value).astype(bool)
        # First, generate the square similarity matrix W = V @ V.T
        W = self._bool_mult(V, V.T)
        # Then, apply recursive power for multi-hop
        for _ in range(steps): 
            W = self._bool_mult(W, W)
        return W

    def get_omnirepresentation(self) -> jnp.ndarray:
        # TKM Omnirepresentación / Matriz por Bloques
        all_objs = [f"{c}:{o}" for c in self.contexts for o in self.contexts[c].objects]
        omni = jnp.zeros((len(all_objs), len(all_objs)), dtype=bool)
        for bridge in self.bridges:
            R = self._bridge_matrices.get(bridge.name)
            if R is not None:
                if_indices = [i for i, x in enumerate(all_objs) if x.startswith(f"{bridge.from_context}:")]
                it_indices = [i for i, x in enumerate(all_objs) if x.startswith(f"{bridge.to_context}:")]
                for ri in range(R.shape[0]):
                    for rj in range(R.shape[1]):
                        if R[ri, rj]: omni = omni.at[if_indices[ri], it_indices[rj]].set(True)
        return omni

    @staticmethod
    def load(path: str) -> UnifiedMatrixEngine:
        with open(path) as f: return UnifiedMatrixEngine.load_from_dict(yaml.safe_load(f))

    @staticmethod
    def load_from_dict(data: dict) -> UnifiedMatrixEngine:
        contexts = {cn: Context(name=cn, objects=list(cd.get("objects", {}).keys()),
                               properties=list(cd.get("properties", {}).keys()),
                               objects_meta=cd.get("objects", {}),
                               properties_meta=cd.get("properties", {}),
                               truths=cd.get("truths", {}))
                    for cn, cd in data.get("contexts", {}).items()}
        bridges = [Bridge(name=bd.get("name", "bridge"), from_context=bd.get("from", ""),
                          to_context=bd.get("to", ""), from_objects=bd.get("from_objects", []),
                          to_objects=bd.get("to_objects", []), relation=bd.get("relation", "has_relation"))
                   for bd in data.get("bridges", [])]
        return UnifiedMatrixEngine(contexts, bridges)

class TKMVisualizer:
    """
    TKM Atom: Grafo_Indice_G.
    Generates specyaml files from the engine state for visualization.
    """
    def __init__(self, engine: UnifiedMatrixEngine):
        self.engine = engine

    def export_knowledge_tree(self, file_path: str):
        """Generates a component diagram of contexts and bridges."""
        spec = {
            "id": "knowledge_tree",
            "title": "TKM Knowledge Tree (Hierarchy of Contexts)",
            "version": "1.0.0",
            "type": "component",
            "data": {
                "nodes": {
                    ctx_name: {
                        "label": f"Context: {ctx_name} (E={self.engine.get_information_energy(ctx_name):.2f})",
                        "kind": "storage"
                    }
                    for ctx_name in self.engine.contexts
                },
                "edges": [
                    {
                        "from": bridge.from_context,
                        "to": bridge.to_context,
                        "relation": "bridge",
                        "label": bridge.name
                    }
                    for bridge in self.engine.bridges
                ]
            }
        }
        with open(file_path, "w") as f:
            yaml.dump(spec, f)

    def export_context_matrix(self, context_name: str, file_path: str):
        """Generates a matrix diagram for a specific context Wi."""
        if context_name not in self.engine.contexts: return
        
        ctx = self.engine.contexts[context_name]
        Vi = self.engine.Vi[context_name]
        Si = self.engine.Si[context_name]
        
        spec = {
            "id": f"matrix_{context_name}",
            "title": f"Operational Matrix: {context_name} (W*)",
            "version": "1.0.0",
            "type": "component_view_matrix",
            "data": {
                "views": [
                    {
                        "id": "full_matrix",
                        "label": "Matrix View",
                        "stages": [
                            {"id": prop, "label": prop} for prop in ctx.properties
                        ]
                    }
                ],
                "components": [
                    {
                        "name": obj,
                        "label": obj,
                        "kind": "core",
                        "stages": {
                            "full_matrix": [
                                prop for j, prop in enumerate(ctx.properties) 
                                if bool(Si[i, j]) and bool(Vi[i, j] == self.engine.M_T.value)
                            ]
                        }
                    }
                    for i, obj in enumerate(ctx.objects)
                ]
            }
        }
        with open(file_path, "w") as f:
            yaml.dump(spec, f)

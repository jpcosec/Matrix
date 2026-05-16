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


class SymbolRegistry:
    """
    TKM Atom: Signo_vs_Simbolo.
    Manages the mapping between internal Symbols (IDs) and external Signs (labels/synonyms).
    """
    def __init__(self):
        self.symbol_to_signs: dict[str, set[str]] = {}
        self.sign_to_symbol: dict[str, str] = {}

    def register_symbol(self, symbol_id: str, initial_sign: str = None):
        if symbol_id not in self.symbol_to_signs:
            self.symbol_to_signs[symbol_id] = set()
        if initial_sign:
            self.add_sign(symbol_id, initial_sign)

    def add_sign(self, symbol_id: str, sign: str):
        if symbol_id not in self.symbol_to_signs:
            self.register_symbol(symbol_id)
        self.symbol_to_signs[symbol_id].add(sign)
        self.sign_to_symbol[sign] = symbol_id

    def get_symbol(self, sign: str) -> str | None:
        return self.sign_to_symbol.get(sign)

    def get_signs(self, symbol_id: str) -> list[str]:
        return list(self.symbol_to_signs.get(symbol_id, []))

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

    def __init__(self, contexts: dict[str, Context] = None, bridges: list[Bridge] = None, registry: SymbolRegistry = None):
        self.contexts = contexts or {}
        self.bridges = bridges or []
        self.registry = registry or SymbolRegistry()
        
        # 4 Structural Masks per Context (TKM Atom: Mascaras_Estructurales)
        self.Vi: dict[str, jnp.ndarray] = {}  # Truth Matrix (Factual)
        self.Si: dict[str, jnp.ndarray] = {}  # Sense Mask (Applicability)
        self.Oi: dict[str, jnp.ndarray] = {}  # Observed Mask (Explicitly seen)
        self.Di: dict[str, jnp.ndarray] = {}  # Discriminative Mask (Reducción Descriptiva)
        
        self._bridge_matrices: dict[str, jnp.ndarray] = {}
        self._build_all_matrices()

    def get_context_mirror(self, context_name: str) -> str:
        """
        Generates a text description of the context for LLM grounding.
        """
        if context_name not in self.contexts:
            return f"Context '{context_name}' does not exist."
        
        ctx = self.contexts[context_name]
        mirror = [f"CONTEXT MIRROR: {context_name}"]
        
        mirror.append("\nOBJECTS (X-Axis):")
        for obj_id in ctx.objects:
            signs = self.registry.get_signs(obj_id)
            meta = ctx.objects_meta.get(obj_id, {})
            mirror.append(f" - Symbol: {obj_id} (Signs: {', '.join(signs)}) | Meta: {meta}")
            
        mirror.append("\nPROPERTIES/DIMENSIONS (Y-Axis):")
        for prop_id in ctx.properties:
            signs = self.registry.get_signs(prop_id)
            meta = ctx.properties_meta.get(prop_id, {})
            mirror.append(f" - Symbol: {prop_id} (Signs: {', '.join(signs)}) | Meta: {meta}")
            
        return "\n".join(mirror)

    def add_dimension(self, context_name: str, symbol_id: str, sign: str = None, meta: dict = None):
        """Adds a new Y-axis dimension to a context."""
        if context_name not in self.contexts: return
        ctx = self.contexts[context_name]
        if symbol_id not in ctx.properties:
            ctx.properties.append(symbol_id)
            ctx.properties_meta[symbol_id] = meta or {}
            if sign:
                self.registry.add_sign(symbol_id, sign)
            self._build_all_matrices()

    def add_object(self, context_name: str, symbol_id: str, sign: str = None, meta: dict = None):
        """Adds a new X-axis object to a context."""
        if context_name not in self.contexts: return
        ctx = self.contexts[context_name]
        if symbol_id not in ctx.objects:
            ctx.objects.append(symbol_id)
            ctx.objects_meta[symbol_id] = meta or {}
            if sign:
                self.registry.add_sign(symbol_id, sign)
            self._build_all_matrices()

    def set_fact(self, context_name: str, subject_id: str, property_id: str, value: bool, mode: str = "M"):
        """Sets a fact in the engine, with different logic for M and G."""
        if context_name not in self.contexts: return
        ctx = self.contexts[context_name]
        
        # G-Mode Logic: Integration Check
        if mode == "G":
            status_info = self.get_status(subject_id, property_id, context_name)
            status = status_info["status"]
            if status == "sinnlos":
                print(f"[TKM-G] Warning: Fact ({subject_id}, {property_id}) is SINNLOS (Tautology/Contradiction). Integration skipped.")
                return
            if status == "unsinnig":
                print(f"[TKM-G] Warning: Fact ({subject_id}, {property_id}) is UNSINNIG (Sense Violation). Integration rejected.")
                return

        # Update truth value
        if subject_id not in ctx.truths:
            ctx.truths[subject_id] = {}
        ctx.truths[subject_id][property_id] = value
        
        # Rebuild matrices for the updated context
        self.Vi[context_name] = self._build_Vi(ctx)
        self.Si[context_name] = self._build_Si(ctx, self.Vi[context_name])
        self.Oi[context_name] = self._build_Oi(ctx)
        self.Di[context_name] = self._build_Di(ctx, self.Vi[context_name])

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
        """
        TKM Atom: Omnirepresentacion (Block Matrix).
        Constructs the unified matrix W = (Colapso(Vi) | Bridges).
        This matrix captures BOTH internal context similarities AND inter-context bridges.
        """
        all_objs = []
        for ctx_name in self.contexts:
            for obj in self.contexts[ctx_name].objects:
                all_objs.append(f"{ctx_name}:{obj}")
        
        N = len(all_objs)
        omni = jnp.zeros((N, N), dtype=bool)
        
        # 1. Internal Context Connections (Dimensional Collapse)
        # This adds the W = V ⊗ V^T for each context into the block diagonal
        current_idx = 0
        for ctx_name in self.contexts:
            W_local = self.dimensional_collapse(ctx_name)
            size = W_local.shape[0]
            omni = omni.at[current_idx:current_idx+size, current_idx:current_idx+size].set(W_local)
            current_idx += size
            
        # 2. Inter-Context Connections (Bridges)
        for bridge in self.bridges:
            R = self._bridge_matrices.get(bridge.name)
            if R is not None:
                if_indices = [i for i, x in enumerate(all_objs) if x.startswith(f"{bridge.from_context}:")]
                it_indices = [i for i, x in enumerate(all_objs) if x.startswith(f"{bridge.to_context}:")]
                for ri in range(R.shape[0]):
                    for rj in range(R.shape[1]):
                        if R[ri, rj]:
                            omni = omni.at[if_indices[ri], it_indices[rj]].set(True)
        return omni

    def dimensional_collapse(self, context_name: str) -> jnp.ndarray:
        """
        TKM Atom: Colapso_Dimensional.
        Collapses a rectangular Object-Property matrix Vi into a square Object-Object 
        Similarity Matrix W = V ⊗ V^T.
        This represents the internal connectivity of objects within a single context.
        """
        if context_name not in self.Vi:
            return None
        Vi = self.Vi[context_name]
        # W[i, j] is true if object i and object j share at least one property
        return self._bool_mult(Vi, Vi.T)

    def recursive_bridge_routing(self, start_context: str, steps: int = 3) -> jnp.ndarray:
        """
        TKM Atom: Enrutamiento_Jerarquico (JAX Optimized).
        Performs multi-hop reasoning across contexts by calculating the recursive 
        boolean power of the Omnirepresentation matrix.
        """
        W = self.get_omnirepresentation()
        
        # Recursive power: W^(2^k) for exponential reach
        # Here we do linear steps for clarity, but JAX makes it fast.
        W_k = W
        for _ in range(steps):
            W_k = self._bool_mult(W_k, W_k)
            # Add self-loops to maintain reachability
            W_k = jnp.logical_or(W_k, jnp.eye(W_k.shape[0], dtype=bool))
            
        return W_k

    def get_collapsed_inference_plane(self) -> dict:
        """
        Returns a high-level view of object reachability across the entire 
        knowledge machine after dimensional collapse.
        """
        W_star = self.recursive_bridge_routing(start_context="", steps=2)
        
        # Map indices back to global (Context, Object) pairs
        all_objects = []
        for ctx_name, ctx in self.contexts.items():
            for obj in ctx.objects:
                all_objects.append(f"{ctx_name}.{obj}")
        
        return {
            "matrix": W_star.tolist(),
            "labels": all_objects
        }

    @staticmethod
    def load(path: str) -> UnifiedMatrixEngine:
        with open(path) as f: return UnifiedMatrixEngine.load_from_dict(yaml.safe_load(f))

    @staticmethod
    def load_from_dict(data: dict) -> UnifiedMatrixEngine:
        registry = SymbolRegistry()
        contexts = {}
        for cn, cd in data.get("contexts", {}).items():
            objs = list(cd.get("objects", {}).keys())
            props = list(cd.get("properties", {}).keys())
            
            # Register initial signs as symbols
            for obj_id in objs: registry.register_symbol(obj_id, obj_id)
            for prop_id in props: registry.register_symbol(prop_id, prop_id)
            
            contexts[cn] = Context(
                name=cn, 
                objects=objs,
                properties=props,
                objects_meta=cd.get("objects", {}),
                properties_meta=cd.get("properties", {}),
                truths=cd.get("truths", {})
            )
            
        bridges = [Bridge(name=bd.get("name", "bridge"), from_context=bd.get("from", ""),
                          to_context=bd.get("to", ""), from_objects=bd.get("from_objects", []),
                          to_objects=bd.get("to_objects", []), relation=bd.get("relation", "has_relation"))
                   for bd in data.get("bridges", [])]
        return UnifiedMatrixEngine(contexts, bridges, registry)

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

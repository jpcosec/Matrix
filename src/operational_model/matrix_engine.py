from dataclasses import dataclass
from typing import Optional
import yaml


@dataclass
class Context:
    name: str
    objects: dict
    properties: dict
    truths: dict
    rules: list

    def __post_init__(self):
        self.object_names = list(self.objects.keys())
        self.property_names = list(self.properties.keys())
        self.n_objects = len(self.object_names)
        self.n_properties = len(self.property_names)


class MatrixEngine:
    def __init__(self, context: Context):
        self.ctx = context
        self.M: dict[str, dict] = {}
        self.S: dict[str, dict] = {}
        self._build_matrices()

    def _build_matrices(self):
        for obj_name, obj_props in self.ctx.truths.items():
            self.M[obj_name] = {}
            self.S[obj_name] = {}
            for prop_name in self.ctx.property_names:
                truth_value = obj_props.get(prop_name)
                if truth_value is not None:
                    self.M[obj_name][prop_name] = truth_value
                else:
                    self.M[obj_name][prop_name] = False

                applicable = self._check_applicability(obj_name, prop_name)
                self.S[obj_name][prop_name] = applicable

    def _check_applicability(self, obj_name: str, prop_name: str) -> bool:
        prop_meta = self.ctx.properties.get(prop_name, {})
        applies_to = prop_meta.get("applies_to")
        if applies_to:
            obj_class = self.ctx.objects.get(obj_name, {}).get("class")
            if obj_class != applies_to:
                return False

        requires = prop_meta.get("applies_if", {}).get("requires")
        if requires:
            req_prop = requires.get("property")
            req_value = requires.get("value")
            if req_prop and req_value is not None:
                current_value = self.M[obj_name].get(req_prop)
                if current_value != req_value:
                    return False
        return True

    def get_status(self, obj_name: str, prop_name: str) -> dict:
        applicable = self.S[obj_name][prop_name]
        truth = self.M[obj_name][prop_name]

        if not applicable:
            return {
                "status": "unsinnig_contextual",
                "applicable": False,
                "truth": None,
                "reason": f"{prop_name} is not applicable to {obj_name}"
            }
        if truth:
            return {
                "status": "sinnvoll",
                "applicable": True,
                "truth": True,
                "reason": "Proposition is applicable and true"
            }
        return {
            "status": "sinnvoll",
            "applicable": True,
            "truth": False,
            "reason": "Proposition is applicable but false"
        }

    def query(self, properties: list[str]) -> list[str]:
        results = []
        for obj_name in self.ctx.object_names:
            match = all(self.M[obj_name].get(p) for p in properties)
            if match:
                results.append(obj_name)
        return results

    def detect_ambiguous(self) -> list[tuple]:
        vectors = {}
        for obj_name in self.ctx.object_names:
            vec = tuple(self.M[obj_name][p] for p in self.ctx.property_names)
            if vec not in vectors:
                vectors[vec] = []
            vectors[vec].append(obj_name)
        return [(objs, vec) for vec, objs in vectors.items() if len(objs) > 1]

    def detect_tautologies(self) -> list[str]:
        tautologies = []
        for prop_name in self.ctx.property_names:
            if all(self.M[obj][prop_name] for obj in self.ctx.object_names):
                tautologies.append(prop_name)
        return tautologies

    @staticmethod
    def load(path: str) -> "MatrixEngine":
        with open(path) as f:
            data = yaml.safe_load(f)
        ctx = Context(
            name=data["context"],
            objects=data["objects"],
            properties=data["properties"],
            truths=data["truths"],
            rules=data.get("rules", [])
        )
        return MatrixEngine(ctx)


def main():
    engine = MatrixEngine.load("examples/vegetales.yaml")
    print(f"Context: {engine.ctx.name}")
    print(f"Matrix M (truth):")
    for obj, props in engine.M.items():
        print(f"  {obj}: {props}")
    print(f"\nMatrix S (sense/applicability):")
    for obj, props in engine.S.items():
        print(f"  {obj}: {props}")

    print(f"\nTautological properties: {engine.detect_tautologies()}")
    print(f"Ambiguous objects: {engine.detect_ambiguous()}")
    print(f"\nQuery [tallo]: {engine.query(['tallo'])}")
    print(f"Query [hoja.rugosa]: {engine.query(['hoja.rugosa'])}")
    print(f"\nStatus 'zanahoria has hoja.rugosa': {engine.get_status('zanahoria', 'hoja.rugosa')}")
    print(f"Status 'espinaca has hoja.rugosa': {engine.get_status('espinaca', 'hoja.rugosa')}")


if __name__ == "__main__":
    main()

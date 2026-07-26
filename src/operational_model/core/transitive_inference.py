"""Matrix-first transitive inference logic."""

from __future__ import annotations

from ..matrices.boolean_matrix import BooleanMatrix
from .fact import Fact
from .proposition import Proposition
from .truth_value import TruthValue


class TransitiveInference:
    """Handles transitive fact generation via Boolean Matrix transitive closure."""

    @staticmethod
    def infer(fact: Fact, others: list[Fact]) -> list[Fact]:
        """Returns facts inferred via matrix transitive closure (MR*)."""
        all_facts = [fact] + list(others)
        rel_id = fact.proposition.relation_id
        same_rel_facts = [f for f in all_facts if f.proposition.relation_id == rel_id]

        # Extract unique domain terms across facts
        terms: set[str] = set()
        for f in same_rel_facts:
            terms.add(f.proposition.subject_symbol_id)
            terms.add(f.proposition.object_symbol_id)

        term_list = sorted(terms)
        if len(term_list) < 2:
            return []

        # Construct relation adjacency matrix MR
        adj = BooleanMatrix.filled(row_axis=term_list, column_axis=term_list, fill=False)
        for f in same_rel_facts:
            if f.truth == TruthValue.TRUE or str(f.truth.value).lower() in ("true", "1"):
                adj.set(f.proposition.subject_symbol_id, f.proposition.object_symbol_id, True)


        # Compute reflexive-transitive closure MR*
        closure = adj.transitive_closure()

        # Identify newly inferred transitive links involving the target fact's subjects/objects
        existing_links = {
            (f.proposition.subject_symbol_id, f.proposition.object_symbol_id)
            for f in same_rel_facts
        }

        target_subj = fact.proposition.subject_symbol_id
        target_obj = fact.proposition.object_symbol_id

        inferred: list[Fact] = []
        for s in term_list:
            for o in term_list:
                if s != o and (s, o) not in existing_links:
                    # Check if (s, o) is derived and connected to target fact's terms
                    if bool(closure.get(s, o)) and (s == target_subj or s == target_obj or o == target_subj or o == target_obj):
                        new_prop = Proposition(
                            relation_id=rel_id,
                            subject_symbol_id=s,
                            object_symbol_id=o,
                            wigame_id=fact.proposition.wigame_id,
                        )
                        inferred.append(Fact(proposition=new_prop, truth=fact.truth))
                        existing_links.add((s, o))

        return inferred


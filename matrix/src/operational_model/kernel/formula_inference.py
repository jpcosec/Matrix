"""Matrix-first inference rules over kernel formulas."""

from __future__ import annotations

from ..matrices.boolean_matrix import BooleanMatrix
from .formula_rewrites import simplify_formula, sort_formula_operands
from .formulas import AndFormula, Formula, IfFormula, NotFormula, OrFormula
from .rule_matrix import RuleMatrixCompiler


def modus_ponens(premises: list[Formula]) -> set[str]:
    """Returns conclusions derivable by Modus Ponens using implication matrix multiplication (v ⊗ I*)."""
    compiled = RuleMatrixCompiler.compile(premises)
    atoms = compiled.atoms
    if not atoms:
        return set()

    # Identify known ground truths in premises (atoms asserted as True)
    premise_sexprs = {_normalize(p).to_sexpr() for p in premises}
    known_vector = [1 if atom in premise_sexprs else 0 for atom in atoms]

    # Compute reflexive-transitive closure of implication matrix I*
    i_closure = compiled.implication_matrix.transitive_closure()

    # Perform Boolean vector-matrix multiplication v ⊗ I*
    conclusions: set[str] = set()
    for col_idx, atom in enumerate(atoms):
        if known_vector[col_idx] == 1:
            continue
        # Atom is derivable if any known_vector[row_idx] == 1 and i_closure[row_idx, col_idx] == True
        is_derivable = any(
            known_vector[row_idx] == 1 and bool(i_closure.get(atoms[row_idx], atom))
            for row_idx in range(len(atoms))
        )
        if is_derivable:
            conclusions.add(atom)

    return conclusions


def conjunction_elimination(premises: list[Formula]) -> set[str]:
    """Returns direct conjuncts derivable from conjunctions."""
    conclusions: set[str] = set()
    for premise in premises:
        simplified = _normalize(premise)
        if isinstance(simplified, AndFormula):
            conclusions.update(item.to_sexpr() for item in simplified.operands)
    return conclusions


def disjunctive_syllogism(premises: list[Formula]) -> set[str]:
    """Returns conclusions derivable from `P∨Q` and `¬P` or `¬Q` via clause matrix propagation."""
    compiled = RuleMatrixCompiler.compile(premises)
    atoms = compiled.atoms
    if not atoms:
        return set()

    premise_sexprs = {_normalize(p).to_sexpr() for p in premises}
    conclusions: set[str] = set()

    c_pos = compiled.positive_clause_matrix
    c_neg = compiled.negative_clause_matrix

    for row_idx, clause_id in enumerate(c_pos.row_axis):
        pos_atoms = [a for a in atoms if c_pos.get(clause_id, a)]
        neg_atoms = [a for a in atoms if c_neg.get(clause_id, a)]

        # If clause is of the form (¬P ∨ Q) and ¬P is falsified because P is known true:
        for neg_atom in neg_atoms:
            if neg_atom in premise_sexprs:
                # ~neg_atom is true, so neg_atom is false. Remaining positive atoms are concluded.
                for pos_atom in pos_atoms:
                    conclusions.add(pos_atom)

        for pos_atom in pos_atoms:
            not_pos = f"(not {pos_atom})"
            if not_pos in premise_sexprs:
                # pos_atom is negated, so other pos_atoms or neg_atoms are concluded
                for other in pos_atoms:
                    if other != pos_atom:
                        conclusions.add(other)

    return conclusions


def hypothetical_syllogism(premises: list[Formula]) -> set[str]:
    """Returns implications derivable from `P→Q` and `Q→R` via matrix closure I*."""
    compiled = RuleMatrixCompiler.compile(premises)
    atoms = compiled.atoms
    if not atoms:
        return set()

    i_closure = compiled.implication_matrix.transitive_closure()
    conclusions: set[str] = set()

    # Original direct implications
    direct_imp = {
        (a1, a2)
        for a1 in atoms
        for a2 in atoms
        if compiled.implication_matrix.get(a1, a2)
    }

    # Transitive implications derived from I*
    for i, a1 in enumerate(atoms):
        for j, a2 in enumerate(atoms):
            if a1 != a2 and bool(i_closure.get(a1, a2)) and (a1, a2) not in direct_imp:
                # Derivable implication (IfFormula a1 a2)
                conclusions.add(f"(if {a1} {a2})")

    return conclusions



def _normalize(formula: Formula) -> Formula:
    """Canonicalizes child order without desugaring implications away."""
    return sort_formula_operands(formula)


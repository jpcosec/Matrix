"""Rule Matrix Compiler: compiles FBF premises into incidence matrices I and (C+, C-)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..matrices.boolean_matrix import BooleanMatrix
from .formula_evaluation import collect_atoms
from .formula_normal_forms import to_cnf
from .formula_rewrites import sort_formula_operands
from .formulas import AndFormula, Formula, IfFormula, NotFormula, OrFormula, RelationAtom, KernelAtom


@dataclass
class CompiledRuleSet:
    """Holds compiled incidence matrices for a formula rule set."""

    atoms: tuple[str, ...]
    implication_matrix: BooleanMatrix
    positive_clause_matrix: BooleanMatrix
    negative_clause_matrix: BooleanMatrix


class RuleMatrixCompiler:
    """Compiles propositional formulas into pure Boolean incidence matrices."""

    @classmethod
    def compile(cls, premises: list[Formula]) -> CompiledRuleSet:
        """Compiles a list of premises into full rule set matrices."""
        atoms = cls.collect_all_atoms(premises)
        imp_matrix = cls.compile_implication_matrix(premises, atoms)
        pos_matrix, neg_matrix = cls.compile_clause_matrices(premises, atoms)
        return CompiledRuleSet(
            atoms=atoms,
            implication_matrix=imp_matrix,
            positive_clause_matrix=pos_matrix,
            negative_clause_matrix=neg_matrix,
        )

    @classmethod
    def collect_all_atoms(cls, premises: list[Formula]) -> tuple[str, ...]:
        """Collects unique sorted atom keys across all premises."""
        atoms: set[str] = set()
        for premise in premises:
            atoms.update(collect_atoms(premise))
        return tuple(sorted(atoms))

    @classmethod
    def compile_implication_matrix(
        cls, premises: list[Formula], atoms: tuple[str, ...]
    ) -> BooleanMatrix:
        """Builds implication matrix I where I[i, j] = True iff P_i => P_j."""
        atom_list = list(atoms)
        matrix = BooleanMatrix.filled(row_axis=atom_list, column_axis=atom_list, fill=False)

        for premise in premises:
            norm = sort_formula_operands(premise)
            if isinstance(norm, IfFormula):
                ant = norm.antecedent.to_sexpr()
                cons = norm.consequent.to_sexpr()
                if ant in atom_list and cons in atom_list:
                    matrix.set(ant, cons, True)
            elif isinstance(norm, OrFormula) and len(norm.operands) == 2:
                # ~A v B is equivalent to A => B
                left, right = norm.operands
                if isinstance(left, NotFormula):
                    ant = left.operand.to_sexpr()
                    cons = right.to_sexpr()
                    if ant in atom_list and cons in atom_list:
                        matrix.set(ant, cons, True)
                elif isinstance(right, NotFormula):
                    ant = right.operand.to_sexpr()
                    cons = left.to_sexpr()
                    if ant in atom_list and cons in atom_list:
                        matrix.set(ant, cons, True)

        return matrix

    @classmethod
    def compile_clause_matrices(
        cls, premises: list[Formula], atoms: tuple[str, ...]
    ) -> tuple[BooleanMatrix, BooleanMatrix]:
        """Builds positive (C+) and negative (C-) clause incidence matrices."""
        atom_list = list(atoms)
        clauses: list[Formula] = []

        for premise in premises:
            cnf = to_cnf(premise)
            if isinstance(cnf, AndFormula):
                clauses.extend(cnf.operands)
            else:
                clauses.append(cnf)

        clause_axis = [f"clause_{i}" for i in range(len(clauses))]
        c_pos = BooleanMatrix.filled(row_axis=clause_axis, column_axis=atom_list, fill=False)
        c_neg = BooleanMatrix.filled(row_axis=clause_axis, column_axis=atom_list, fill=False)

        for idx, clause in enumerate(clauses):
            clause_id = clause_axis[idx]
            literals = clause.operands if isinstance(clause, OrFormula) else [clause]
            for lit in literals:
                if isinstance(lit, NotFormula):
                    atom_key = lit.operand.to_sexpr()
                    if atom_key in atom_list:
                        c_neg.set(clause_id, atom_key, True)
                else:
                    atom_key = lit.to_sexpr()
                    if atom_key in atom_list:
                        c_pos.set(clause_id, atom_key, True)

        return c_pos, c_neg

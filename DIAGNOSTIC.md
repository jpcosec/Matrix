# Matrix Engine — Full Repository Diagnostic

**Date:** 2026-05-19
**Head:** c1e8cf1
**Branch:** main (clean, no uncommitted changes)
**Total commits:** 49

---

## 1. Executive Summary

Matrix v0.1.0 is a **functional but early-stage research prototype**. The core engine (proposition-first operational model with boolean matrices, kernel algebra, s-expression runtime, routing, and YAML persistence) works — all 114 tests pass. The code is cleanly typed (100% type annotations) and well-documented at the module/class level. However, the **code does not follow its own coding standards**, documentation describes intent more than implemented reality, and there is zero developer infrastructure (no CI, no linting, no API docs, no coverage).

---

## 2. What Works Well

| Area | Status | Evidence |
|------|--------|----------|
| **Tests pass** | ✅ All 114 pass | `pytest` — 0.16s full suite |
| **Type annotations** | ✅ 100% | All 226 functions annotated |
| **Module/class docstrings** | ✅ 100% | All 52 files, 41 classes |
| **Package installs cleanly** | ✅ | `pip install -e .` succeeds |
| **YAML persistence** | ✅ | 7 example WiGame YAML files load correctly |
| **Shrdlu prototype** | ✅ | 14 tests pass, proto module loads |
| **Git hygiene** | ✅ | Clean working tree, single remote, systematic history |
| **DESK workflow** | ✅ | Well-organized task tracking with procedure, rituals, spec |
| **No syntax errors** | ✅ | All 52 source files parse clean |
| **No TODOs/FIXMEs** | ✅ | Zero unresolved markers in source |

---

## 3. Test Health

**All 114 tests pass** across 27 test files in 0.16s. No JAX-dependent tests appear to be present or tested.

**Coverage by area:**

| Area | Files | Tests |
|------|-------|-------|
| Kernel (boolean, bitwise, rewrites, inference, normal forms) | 6 | ~35 |
| Propositional grammar & evaluator | 2 | ~15 |
| Operational model (WiGame, routing, projections) | 3 | ~15 |
| S-expression runtime | 1 | ~12 |
| Serialization round-trip | 1 | 2 |
| Dimensional collapse | 1 | 4 |
| Information energy | 1 | 3 |
| Relation algebra, validation, semantics, identity | 4 | ~12 |
| Shrdlu (dialog, parser, lexicon, lowering) | 4 | 14 |
| Status evaluation | 1 | ~4 |
| Boolean subsumption | 1 | 2 |

**Gaps:**
- Serialization round-trip has only 2 tests for a critical path
- No CI configuration (`.github/workflows/` absent)
- No coverage measurement
- No performance/benchmark tests

---

## 4. Documentation Audit

### 4.1 What exists

11 docs in `docs/` covering architecture, concepts, data models, operations, canonical forms, kernel symbol policy, storage boundary, coding standards, and rebuild/migration policy.

### 4.2 Broken references

- `docs/operations.md:92` references `tests/test_tkm_roundtrip_suite.py` — **file does not exist**

### 4.3 Docstring compliance (vs. own coding standards)

| Standard | Requirement | Actual | Status |
|----------|-------------|--------|--------|
| Module docstring | Every file | 52/52 (100%) | ✅ |
| Class docstring | Every class | 41/41 (100%) | ✅ |
| Function docstring | Every function | 174/226 (76%) | ❌ |

**52 undocumented functions** — concentrated in:
- `s_expression_runtime.py` (12 missing, all private methods)
- `vi_matrix.py`, `si_matrix.py` (to_dict/from_dict)
- `symbol_spaces.py` (canonicalize, assert_equivalent, assert_instance, etc.)
- `formula_rewrites.py` (private helpers)
- `bitwise_execution.py` (mask helpers)

### 4.4 Accuracy issues

Docs consistently use aspirational language ("should", "intended direction", "target") without marking what is actually implemented. A new reader cannot distinguish between:
- Proven behavior (tests exist)
- Stub/pending (code exists but may be incomplete)
- Future design (not yet implemented)

---

## 5. Coding Standards Compliance Audit

The `docs/coding_standards.md` defines specific rules. Here is the compliance:

### 5.1 File size: "max 80 lines"

| Status | Count | Detail |
|--------|-------|--------|
| Compliant | 32 files | Under 80 lines |
| **Violating** | **20 files** | See below |

Largest offenders:
- **393 lines** — `s_expression_runtime.py` (5x limit)
- 157 lines — `src/__init__.py` (re-exports)
- 151 lines — `src/operational_model/__init__.py` (re-exports)
- 145 lines — `kernel/formulas.py`
- 139 lines — `system/wi_game_serialization.py`
- 129 lines — `system/wigame.py`
- 122 lines — `system/logical_system.py`
- 121 lines — `routing/routing_projection.py`
- 117 lines — `kernel/formula_rewrites.py`
- 111 lines — `system/wi_game_queries.py`
- 107 lines — `kernel/__init__.py`
- 106 lines — `matrices/boolean_matrix.py`

### 5.2 Functions: "max 8 lines"

**30+ functions exceed 8 lines.** Worst:
- `s_expression_runtime.py:_eval_assert` — **51 lines**
- `s_expression_runtime.py:_eval_check` — **36 lines**
- `s_expression_runtime.py:_fact_groups` — **23 lines**
- `s_expression_runtime.py:_matches_selectors` — **21 lines**

### 5.3 Classes: "max 2 methods"

| Status | Count | Examples |
|--------|-------|----------|
| Compliant | 32 classes | 2 or fewer methods |
| **Violating** | **9 classes** | See below |

- `SExpressionRuntime` — **21 methods** (god object)
- `WiGame` — **17 methods**
- `BooleanMatrix` — **13 methods**
- `LogicalSystem` — **13 methods**
- `RelationAlgebra` — **9 methods**
- `RoutingProjection` — **9 methods**
- `SymbolSpace` — **6 methods**
- `ViMatrix` — **6 methods**
- `SiMatrix` — **4 methods**

### 5.4 "1 class per file"

| Status | Count | Files |
|--------|-------|-------|
| Compliant | 35 files | Single class |
| **Violating** | **3 files** | `formulas.py` (8 classes), `operation_results.py` (3 classes), `s_expression_runtime.py` (2 classes) |

### 5.5 "folders >5 files → subfolders"

**Compliant.** Max files per folder: `system/` (10), `kernel/` (10).

---

## 6. Package & Build Issues

| Issue | Detail |
|-------|--------|
| **`setup.py` missing `where='src'`** | `find_packages()` without `package_dir` or `where='src'` means it discovers packages from root, not `src/`. Works via editable install but may break in non-editable builds. |
| **No `pyproject.toml`** | Build system metadata not declared. Relies on implicit setuptools. |
| **`.gitignore` incomplete** | Missing `*.egg-info/`, `dist/`, `build/`, `.eggs/`, `.tox/`, `.coverage`, `htmlcov/`, `.mypy_cache/`, `.ruff_cache/`, `.venv/` |
| **No CI** | No `.github/workflows/` — no automated test running, no linting, no type-checking |
| **No linter config** | No `ruff.toml`, `.flake8`, `pyproject.toml` with tool config |
| **No type checker config** | No `pyrightconfig.json` or `mypy.ini` |
| **Single runtime dependency** | Only `pyyaml` — good for prototype, but JAX is listed as optional with no install path |

---

## 7. Dead / Questionable Artifacts

| File | Issue |
|------|-------|
| `roundtrip_test_state.json` (3KB) | Appears to be a legacy TKM test fixture. No source code references it. Possibly dead. |
| `DESK/tasks/Board.md` | Shows **no active tasks**. The `task-db-04-test-yaml-persistence.md` task is present in the tasks folder but not referenced from Board. The Board may be stale. |
| `DESK/tasks/task-db-04-test-yaml-persistence.md` | Task file references `docs/storage_boundary.md` but this was already added in the latest commit. Task may be resolved but not cleaned up per procedure rules. |

---

## 8. Code Structure Concerns

### 8.1 `SExpressionRuntime` (393 lines, 21 methods)

This is a clear **god object**. It handles parsing s-expressions, creating symbols/relations/li-spaces/wigames, checking/asserting/ingesting propositions, returning facts, resolving selectors, and managing the logical system. It should be split into focused collaborators.

### 8.2 `formulas.py` (8 classes, 145 lines)

Containers for the formula AST (`Formula`, `RelationAtom`, `KernelAtom`, `ConstantFormula`, `NotFormula`, `AndFormula`, `OrFormula`, `IfFormula`). These are small and could reasonably stay together, but it violates the stated standard.

### 8.3 `__init__.py` re-export chains

Both `src/__init__.py` (157 lines) and `src/operational_model/__init__.py` (151 lines) are mostly re-export lists. This is fine for a public API surface but adds noise.

### 8.4 ∅ (Unicode empty set) in YAML

Example YAML files use `∅` (U+2205) as a void marker in matrix values and fact truth fields. This works with `yaml.safe_load` since it's inside quoted strings, but:
- It may cause issues with databases (Postgres)
- It is error-prone to type and copy
- It is inconsistent: sometimes used as a bare YAML value (line 90: `truth: ∅`), sometimes inside strings (line 36: `'010∅∅'`)

---

## 9. Shrdlu Prototype Assessment

| Module | Exports | Status |
|--------|---------|--------|
| `lexicon.py` | `LexiconEntry`, `LexiconToken`, `ShrdluLexicon` | ✅ Works |
| `english_parser.py` | `ParseError`, `TokenStream` | ✅ Works |
| `semantic_frames.py` | `EntityDescriptor`, `RelationFrame`, `SemanticFrame`, `ImperativeFrame`, `QueryFrame` | ✅ Works |
| `lowering.py` | `SceneObject`, `PrototypeHarness` | ✅ Works |
| `dialog_state.py` | `DialogState` | ✅ Works |
| `proto.py` | `main` | ✅ Works |

**Public API name mismatch:** The README and docs reference `EnglishParser` but the actual class is `TokenStream`. `Lowering` is referenced in docs but the class is `PrototypeHarness`. The docs give wrong class names.

---

## 10. Recommendations by Severity

### Critical
1. Fix `setup.py` to use `find_packages(where='src')` and `package_dir={'': 'src'}` — the package may break in non-editable installs

### High
2. Add CI (GitHub Actions) — run `pytest` on every push/PR
3. Split `SExpressionRuntime` into focused modules
4. Fix broken doc reference (`docs/operations.md:92` → correct test path)
5. Remove or clearly mark dead artifact `roundtrip_test_state.json`
6. Add type checker and linter configs (mypy or pyright, ruff or flake8)

### Medium
7. Document undocumented functions (52 missing)
8. Clean up DESK board — either close `task-db-04` or add it to Board
9. Update Shrdlu docs to use correct class names (`TokenStream` not `EnglishParser`, `PrototypeHarness` not `Lowering`)
10. Standardize the ∅ character usage in YAML (document it or replace with null/empty string)
11. Expand serialization round-trip tests (only 2 exist for a critical persistence path)
12. Add `.gitignore` entries for build artifacts

### Low
13. Break up oversized files (>80 lines) per own standards
14. Reduce classes with >2 methods per own standards
15. Mark aspirational doc content clearly (e.g., "**Future:**" labels)
16. Add coverage measurement and set a baseline
17. Add developer onboarding section to docs

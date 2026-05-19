# Task Board

## Active Tasks

- **task-core-01-doc-and-legacy-sync** - clean remaining architectural drift around `Si`, `Oi`, and the stale runtime surfaces; see `DESK/tasks/task-core-01-doc-and-legacy-sync.md`
- **task-prop-01-grammar-and-precedence** - define the well-formed propositional s-expression grammar and precedence policy for the kernel; see `DESK/tasks/task-prop-01-grammar-and-precedence.md`
- **task-prop-02-evaluator-and-classification** - evaluate propositional formulas as truth functions over SixVi and classify them semantically; see `DESK/tasks/task-prop-02-evaluator-and-classification.md`
- **task-prop-03-rewrites-normal-forms-and-inference** - add rewrite laws, normal forms, and a first propositional inference layer; see `DESK/tasks/task-prop-03-rewrites-normal-forms-and-inference.md`
- **task-bool-01-boolean-algebra-kernel** - add the Boolean-algebra layer for simplification, subsumption, duality, and matrix-friendly reduction over kernel formulas; see `DESK/tasks/task-bool-01-boolean-algebra-kernel.md`
- **task-bool-02-truth-tables-and-bit-basis** - model the 16 binary Boolean functions explicitly so the kernel has a stable table/bit basis for connective execution and derived inference; see `DESK/tasks/task-bool-02-truth-tables-and-bit-basis.md`
- **task-bool-03-bitwise-matrix-execution** - lower kernel connectives and reductions to bitwise or matrix-friendly execution primitives for SixVi; see `DESK/tasks/task-bool-03-bitwise-matrix-execution.md`
- **task-runtime-02-s-expression-authoring-surface** - extend the canonical runtime from fact checking to symbol, relation, LiSpace, and WiGame authoring; see `DESK/tasks/task-runtime-02-s-expression-authoring-surface.md`
- **task-kernel-02-lowering-and-db-spaces** - operationalize `instance` and `equivalent` as kernel lowering primitives over DB-backed symbol spaces; see `DESK/tasks/task-kernel-02-lowering-and-db-spaces.md`
- **task-rel-02-validation-routing-and-identity** - use relation semantics for sense validation, routing hooks, reduction hooks, and equivalence-aware fact identity; see `DESK/tasks/task-rel-02-validation-routing-and-identity.md`
- **task-proto-shrdlu-02-lowering-and-dialog** - turn the separate SHRDLU prototype into a real client of the kernel with lowering, ambiguity, and a tiny execution harness; see `DESK/tasks/task-proto-shrdlu-02-lowering-and-dialog.md`
- **task-storage-01-postgres-compatibility** - define the persistence boundary so the current prototype stays YAML-first while remaining compatible with future Postgres-backed symbol spaces; see `DESK/tasks/task-storage-01-postgres-compatibility.md`

## Deferred / Future

- Future tasks should be split from the active files above only when new scope appears beyond this session backlog.

## Execution Rule

Before starting a task, check:
1. Are the exact files listed?
2. Are the documentation references listed explicitly?
3. Is every touched legacy surface marked `migrate`, `delete`, or `defer`?
4. Is the validation command concrete?
5. Does the task strengthen the new architecture instead of preserving the old one?

If any answer is no, improve the task first.

# Task Board

## Active Tasks

(None)

## Deferred / Future

- **Si redesign** — see `docs/proposition_first_architecture.md`
- **Remove residual `Oi` references** — `Oi` should not survive as a structural matrix; clean remaining docs and terminology drift, see `docs/proposition_first_architecture.md`
- **New ingestion CLI** — see `docs/canonical_forms_and_ingestion.md`
- **Direct s-expression ingestor** — parse canonical proposition text `(R a b)` into proposition-first runtime objects, see `docs/canonical_forms_and_ingestion.md` and `docs/operations.md`
- **S-expression runtime step 2: registry authoring** — add canonical forms for creating symbols and relations directly from the runtime surface
- **S-expression runtime step 3: Wi authoring** — add canonical forms for creating `LiSpace` and `WiGame` structures without falling back to YAML editing
- **S-expression runtime step 4: inference surface** — add canonical `infer` forms over resolved facts and local games
- **Kernel step 2: typed assertion lowering** — teach the runtime how `instance` and `equivalent` operationalize symbol spaces and DB-backed normalization
- **Kernel step 3: connective execution** — add execution semantics for `and`, `or`, `not`, and `if` over canonical forms
- **Relation step 2: sense-aware relation validation** — use relation semantics to participate in proposition admissibility and sense evaluation
- **Relation step 3: routing and reduction hooks** — expose relation semantics to dimensional reduction and context-routing decisions
- **Proto-SHRDLU step 2: frame lowering** — lower `prototypes/shrdlu/` semantic frames into canonical runtime operations
- **Proto-SHRDLU step 3: discourse and ambiguity** — add explicit unresolved-reference handling for `it`, `them`, and competing noun-phrase matches inside the separate prototype package
- **Proto-SHRDLU step 4: planner/world harness** — add a tiny test world only to validate command execution over parsed frames in the prototype package
- **README and runtime surface sync** — fix stale references such as the missing `cli.py` entrypoint and legacy `Oi` wording in `README.md`
- **Postgres compatibility path** — stay full YAML for the prototype, but keep future storage work compatible with Postgres and graph-oriented extensions

## Execution Rule

Before starting a task, check:
1. Are the exact files listed?
2. Are the documentation references listed explicitly?
3. Is every touched legacy surface marked `migrate`, `delete`, or `defer`?
4. Is the validation command concrete?
5. Does the task strengthen the new architecture instead of preserving the old one?

If any answer is no, improve the task first.

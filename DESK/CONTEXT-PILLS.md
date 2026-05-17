# Context Pills

Context pills exist to eliminate ambiguity.

They are not just ADRs and they are not loose notes.

Each pill must be atomized enough to explain one narrow decision surface in terms of:

- what
- why
- how
- what for

The purpose is to prevent drift:

- drift between tasks
- drift between code and architecture
- drift between two agents working in parallel
- drift where a decision taken in one place disappears in another

## Pill Rules

- One pill should explain one decision, one boundary, or one contract.
- If a pill explains two unrelated decisions, split it.
- A task must reference only the pills required to remove ambiguity for that task.
- If a task still requires improvisation after reading its pills, either the task or the pills are underspecified.

## Required Shape

Every pill should contain:

1. `What`
2. `Why`
3. `How`
4. `What For`
5. `Applies To`
6. `Does Not Apply To`
7. `Failure Modes`

## Indexing Rule

- Pills must be individually referenceable from tasks.
- Tasks must list pills explicitly.
- Tasks should avoid ambient assumptions not captured by pills.

## Parallelization Rule

The pill system exists partly to make parallel work safe.

If pills and tasks are granular enough, separate agents should be able to execute different tasks in parallel without contaminating each other's context.

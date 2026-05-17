# Context References

Context references exist to eliminate ambiguity before implementation starts.

They are not scratch notes and they are not task-local reminders. They should point to stable documentation that already captures the relevant decision surface.

## Reference Rules

- A task should reference only the documents needed to remove ambiguity for that task.
- If the needed context is still fragmented across temporary notes, consolidate it into `docs/` before or alongside the task.
- If a task still requires improvisation after reading its references, either the task or the documentation is underspecified.
- DESK should not accumulate architecture fragments that belong in permanent documentation.

## Expected Reference Shape

Each referenced document should explain, as needed:

1. what
2. why
3. how
4. boundaries
5. failure modes

## Indexing Rule

- Documents referenced from tasks must be stable and path-addressable.
- Tasks must list references explicitly.
- Tasks should avoid ambient assumptions not captured by the cited docs.

## Parallelization Rule

Parallel work is only safe when tasks depend on explicit, shared references instead of hidden context.

If the references and tasks are granular enough, separate agents should be able to execute different tasks in parallel without contaminating each other's context.

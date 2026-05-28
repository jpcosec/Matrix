# Context Pill

One atomic unit of context — the smallest self-contained piece of knowledge
needed by a subagent working on a task.

## Fields

| Field | Purpose |
|-------|---------|
| **Why** | Why does this entity exist? What problem does it solve? |
| **What** | Brief definition. What is it? |
| **Where** | File paths, line refs (for `implemented`). Module/class name (for `to-implement`). |
| **How** | Shared patterns, conventions, standards, naming rules. |
| **How Not** | Anti-patterns, pitfalls, things explicitly to avoid. |
| **Why (depth)** | Deeper design rationale, trade-offs made, alternatives rejected. |

## Header

```
---
id: pill-<NNN>-<kebab-case-slug>
entity: <the artifact or concept>
status: implemented | to-implement
---
```

## Rules

1. **Atomic** — one concept per pill.
2. **Reusable** — same pill can be referenced from many tasks.
3. **Non-contradictory** — if two pills conflict, update or remove one.
4. **Modular** — a pill must stand alone; no cross-pill dependencies.
5. **To-implement pills** *must* contain patterns, standards, and naming rules.
6. **Implemented pills** *must* point to code (file:line).
7. Pills **do not replace** task files — tasks say *what to do*, pills say *what the subagent needs to know to do it*.
8. Pills are **ephemeral** — once the relevant code area is documented in proper docs, the pill is absorbed and deleted.

## Lifecycle

1. Created when a task is registered or when context gaps are identified.
2. Referenced from the task's "Context Pills" section in its TASK-SPEC.
3. Loaded by subagents to bootstrap without reading the full codebase.
4. Deleted when the area of code is stable and fully documented.

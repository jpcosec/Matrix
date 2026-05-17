# Rituals

This file defines the active work rituals for Matrix rebuild work.

## Core Rules

- No task is complete without tests or an explicit reason why tests do not apply.
- `DESK/tasks/` contains only active work.
- Legacy code is not protected by sentiment; keep only what the new architecture actually needs.
- If a legacy surface is useful, migrate the behavior into the new model instead of extending the old stack.

## Rebuild Ritual

Before changing architecture:

1. AUDIT - Confirm what is legacy, what is active, and what still has users.
2. CLASSIFY - Mark each legacy surface as `migrate`, `delete`, or `defer`.
3. ISOLATE - Extract useful logic into new modules before deleting the old container.
4. NAME - Normalize terminology before adding abstractions.
5. TEST - Update or replace tests around the new model.
6. IMPLEMENT - Change the smallest surface that moves the rebuild forward.
7. VERIFY - Re-run the relevant tests.

## Scope Discipline

- One task should be completable in one focused session.
- If a task mixes migration, deletion, and redesign at once, split it.
- Do not repair legacy tests just to preserve the old architecture.
- Do not add new features to legacy runtime surfaces.

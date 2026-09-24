---
kind: unclear
sender_project: Matrix
created_at: 2026-07-27T02:20:56
status: closed
---

# Fallo en status y doctor repair

El comando deskops status --root . falla por documentos no trackeados (ej. desk/drawer/triage_cleanup_plan.md). deskops doctor --repair no los arregla y pide ejecutar sldb docs track manualmente, pero este pide un argumento --model no especificado.

## Resolution

Two separate problems were behind this note.

**`sldb docs track` needing `--model`.** That is not a missing argument, it is the
required one. The command is `sldb docs track --model TaskDoc <path>`. Untracking
and re-tracking with the explicit model is also how a stale `hash_d`
(`data_mutation`) is repaired, which was the actual blocker here.

**`deskops doctor --repair` not fixing `desk/rituals/phase.md`.** This one is a
deskops bug, not a Matrix one. `doctor` requires the file
(`deskops/cli/commands/doctor.py:35`) but `scaffold_desk()`
(`deskops/workspace.py:194-233`) never creates it: it writes `execution.md`,
`testing.md` and `closeout.md` and no `phase.md`. So the finding can never be
repaired from inside this repo. Reported upstream rather than worked around by
faking the file.

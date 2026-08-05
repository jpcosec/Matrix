---
kind: unclear
sender_project: Matrix
created_at: 2026-07-27T02:20:56
status: open
---

# Fallo en status y doctor repair

El comando deskops status --root . falla por documentos no trackeados (ej. desk/drawer/triage_cleanup_plan.md). deskops doctor --repair no los arregla y pide ejecutar sldb docs track manualmente, pero este pide un argumento --model no especificado.

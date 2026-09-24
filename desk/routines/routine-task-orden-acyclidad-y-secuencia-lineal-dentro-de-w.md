---
# routine-xxx
id: routine-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w
# active | archived
status: active
# Initial node identifier
entrypoint: checklist-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-execution-ready
# Ordered or grouped primitive identifiers
decomposition:
- checklist-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-execution-ready
- operator-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-activate
- checklist-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-testing-ready
- operator-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-ready-for-testing
- checklist-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-closeout-ready
- operator-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-close
# Edge identifiers composing the graph
edges:
- edge-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-execution-to-activate
- edge-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-activate-to-testing
- edge-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-testing-to-ready
- edge-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-ready-to-closeout
- edge-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-closeout-to-close
- edge-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-close-to-complete
# Terminal node identifiers
terminal_nodes:
- complete
# e.g., system:deskops
tags:
- workspace:desk
- primitive:routine
---

# Routine for Orden: acyclidad y secuencia lineal dentro de W

## Summary

_Summarize what this routine does and how its nodes fit together._

Actionable routine for Orden: acyclidad y secuencia lineal dentro de W.

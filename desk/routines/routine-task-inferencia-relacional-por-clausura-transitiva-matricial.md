---
# routine-xxx
id: routine-task-inferencia-relacional-por-clausura-transitiva-matricial
# active | archived
status: active
# Initial node identifier
entrypoint: checklist-task-inferencia-relacional-por-clausura-transitiva-matricial-execution-ready
# Ordered or grouped primitive identifiers
decomposition:
- checklist-task-inferencia-relacional-por-clausura-transitiva-matricial-execution-ready
- operator-task-inferencia-relacional-por-clausura-transitiva-matricial-activate
- checklist-task-inferencia-relacional-por-clausura-transitiva-matricial-testing-ready
- operator-task-inferencia-relacional-por-clausura-transitiva-matricial-ready-for-testing
- checklist-task-inferencia-relacional-por-clausura-transitiva-matricial-closeout-ready
- operator-task-inferencia-relacional-por-clausura-transitiva-matricial-close
# Edge identifiers composing the graph
edges:
- edge-task-inferencia-relacional-por-clausura-transitiva-matricial-execution-to-activate
- edge-task-inferencia-relacional-por-clausura-transitiva-matricial-activate-to-testing
- edge-task-inferencia-relacional-por-clausura-transitiva-matricial-testing-to-ready
- edge-task-inferencia-relacional-por-clausura-transitiva-matricial-ready-to-closeout
- edge-task-inferencia-relacional-por-clausura-transitiva-matricial-closeout-to-close
- edge-task-inferencia-relacional-por-clausura-transitiva-matricial-close-to-complete
# Terminal node identifiers
terminal_nodes:
- complete
# e.g., system:deskops
tags:
- workspace:desk
- primitive:routine
---

# Routine for Inferencia Relacional por Clausura Transitiva Matricial

## Summary

_Summarize what this routine does and how its nodes fit together._

Actionable routine for Inferencia Relacional por Clausura Transitiva Matricial.

---
# routine-xxx
id: routine-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio
# active | archived
status: active
# Initial node identifier
entrypoint: checklist-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-execution-ready
# Ordered or grouped primitive identifiers
decomposition:
- checklist-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-execution-ready
- operator-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-activate
- checklist-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-testing-ready
- operator-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-ready-for-testing
- checklist-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-closeout-ready
- operator-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-close
# Edge identifiers composing the graph
edges:
- edge-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-execution-to-activate
- edge-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-activate-to-testing
- edge-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-testing-to-ready
- edge-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-ready-to-closeout
- edge-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-closeout-to-close
- edge-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-close-to-complete
# Terminal node identifiers
terminal_nodes:
- complete
# e.g., system:deskops
tags:
- workspace:desk
- primitive:routine
---

# Routine for Proyeccion objeto-sujeto: encadenar por termino medio

## Summary

_Summarize what this routine does and how its nodes fit together._

Actionable routine for Proyeccion objeto-sujeto: encadenar por termino medio.

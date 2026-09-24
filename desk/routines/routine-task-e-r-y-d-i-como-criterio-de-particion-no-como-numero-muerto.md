---
# routine-xxx
id: routine-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto
# active | archived
status: active
# Initial node identifier
entrypoint: checklist-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-execution-ready
# Ordered or grouped primitive identifiers
decomposition:
- checklist-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-execution-ready
- operator-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-activate
- checklist-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-testing-ready
- operator-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-ready-for-testing
- checklist-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-closeout-ready
- operator-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-close
# Edge identifiers composing the graph
edges:
- edge-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-execution-to-activate
- edge-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-activate-to-testing
- edge-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-testing-to-ready
- edge-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-ready-to-closeout
- edge-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-closeout-to-close
- edge-task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto-close-to-complete
# Terminal node identifiers
terminal_nodes:
- complete
# e.g., system:deskops
tags:
- workspace:desk
- primitive:routine
---

# Routine for E(R) y D_i como criterio de particion, no como numero muerto

## Summary

_Summarize what this routine does and how its nodes fit together._

Actionable routine for E(R) y D_i como criterio de particion, no como numero muerto.

---
# routine-xxx
id: routine-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor
# active | archived
status: active
# Initial node identifier
entrypoint: checklist-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-execution-ready
# Ordered or grouped primitive identifiers
decomposition:
- checklist-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-execution-ready
- operator-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-activate
- checklist-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-testing-ready
- operator-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-ready-for-testing
- checklist-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-closeout-ready
- operator-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-close
# Edge identifiers composing the graph
edges:
- edge-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-execution-to-activate
- edge-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-activate-to-testing
- edge-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-testing-to-ready
- edge-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-ready-to-closeout
- edge-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-closeout-to-close
- edge-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-close-to-complete
# Terminal node identifiers
terminal_nodes:
- complete
# e.g., system:deskops
tags:
- workspace:desk
- primitive:routine
---

# Routine for BlockMatrix desde el LogicalSystem: ensamblar el hipertensor

## Summary

_Summarize what this routine does and how its nodes fit together._

Actionable routine for BlockMatrix desde el LogicalSystem: ensamblar el hipertensor.

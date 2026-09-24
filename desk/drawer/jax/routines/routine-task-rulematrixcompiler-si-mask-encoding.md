---
# routine-xxx
id: routine-task-rulematrixcompiler-si-mask-encoding
# active | archived
status: archived
# Initial node identifier
entrypoint: checklist-task-rulematrixcompiler-si-mask-encoding-execution-ready
# Ordered or grouped primitive identifiers
decomposition:
- checklist-task-rulematrixcompiler-si-mask-encoding-execution-ready
- operator-task-rulematrixcompiler-si-mask-encoding-activate
- checklist-task-rulematrixcompiler-si-mask-encoding-testing-ready
- operator-task-rulematrixcompiler-si-mask-encoding-ready-for-testing
- checklist-task-rulematrixcompiler-si-mask-encoding-closeout-ready
- operator-task-rulematrixcompiler-si-mask-encoding-close
# Edge identifiers composing the graph
edges:
- edge-task-rulematrixcompiler-si-mask-encoding-execution-to-activate
- edge-task-rulematrixcompiler-si-mask-encoding-activate-to-testing
- edge-task-rulematrixcompiler-si-mask-encoding-testing-to-ready
- edge-task-rulematrixcompiler-si-mask-encoding-ready-to-closeout
- edge-task-rulematrixcompiler-si-mask-encoding-closeout-to-close
- edge-task-rulematrixcompiler-si-mask-encoding-close-to-complete
# Terminal node identifiers
terminal_nodes:
- complete
# e.g., system:deskops
tags:
- workspace:desk
- primitive:routine
---

# Routine for RuleMatrixCompiler: Si Mask Encoding

## Summary

_Summarize what this routine does and how its nodes fit together._

Actionable routine for RuleMatrixCompiler: Si Mask Encoding.

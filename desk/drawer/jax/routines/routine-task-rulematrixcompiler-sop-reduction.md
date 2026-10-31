---
# routine-xxx
id: routine-task-rulematrixcompiler-sop-reduction
# active | archived
status: archived
# Initial node identifier
entrypoint: checklist-task-rulematrixcompiler-sop-reduction-execution-ready
# Ordered or grouped primitive identifiers
decomposition:
- checklist-task-rulematrixcompiler-sop-reduction-execution-ready
- operator-task-rulematrixcompiler-sop-reduction-activate
- checklist-task-rulematrixcompiler-sop-reduction-testing-ready
- operator-task-rulematrixcompiler-sop-reduction-ready-for-testing
- checklist-task-rulematrixcompiler-sop-reduction-closeout-ready
- operator-task-rulematrixcompiler-sop-reduction-close
# Edge identifiers composing the graph
edges:
- edge-task-rulematrixcompiler-sop-reduction-execution-to-activate
- edge-task-rulematrixcompiler-sop-reduction-activate-to-testing
- edge-task-rulematrixcompiler-sop-reduction-testing-to-ready
- edge-task-rulematrixcompiler-sop-reduction-ready-to-closeout
- edge-task-rulematrixcompiler-sop-reduction-closeout-to-close
- edge-task-rulematrixcompiler-sop-reduction-close-to-complete
# Terminal node identifiers
terminal_nodes:
- complete
# e.g., system:deskops
tags:
- workspace:desk
- primitive:routine
---

# Routine for RuleMatrixCompiler: SOP Reduction

## Summary

_Summarize what this routine does and how its nodes fit together._

Actionable routine for RuleMatrixCompiler: SOP Reduction.

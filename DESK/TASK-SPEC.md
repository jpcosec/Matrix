# Task Spec

This file defines the minimum shape required for an executable Matrix rebuild task.

## Required Sections

Every non-trivial task should contain:

1. `Goal`
2. `Objective`
3. `Non-Goals`
4. `Pills Required`
5. `References`
6. `Exact Files To Change`
7. `Files To Avoid Unless Necessary`
8. `Delete / Migrate Decision`
9. `End State`
10. `Exit Criteria`
11. `Suggested Implementation Path`
12. `Validation`
13. `Failure Modes`

## Minimum Semantics

### Goal

Why this task exists at all.

### Objective

What must become true.

### Non-Goals

What this task must not absorb.

### Pills Required

Only the pills needed to eliminate ambiguity for this task.

### Delete / Migrate Decision

The task must explicitly state whether each touched legacy surface is being:

- migrated
- deleted
- deferred

### Validation

Concrete commands, checks, or artifacts that prove success.

## Anti-Patterns

- task says only "clean legacy"
- task does not list files
- task does not list pills
- task does not distinguish migrate vs delete
- task repairs old tests without improving the new architecture

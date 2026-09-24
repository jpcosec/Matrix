# Upstream: deskops doctor requires a file scaffold_desk never writes

ID: task-deskops-scaffold-phase-md
Status: deferred
Priority: low

## Rationale

Not a Matrix bug. Reported here so it is not rediscovered a third time.

`deskops/cli/commands/doctor.py:35` requires `desk/rituals/phase.md`:

```python
if not (desk_dir / "rituals" / "phase.md").exists():
    missing_desk_files.append("desk/rituals/phase.md")
```

`scaffold_desk()` in `deskops/workspace.py:194-233` writes `config.json`,
`tasks/Board.md`, `contexts/pills.md`, `rituals/execution.md`,
`rituals/testing.md`, `rituals/closeout.md`, `drawer/README.md` and
`atoms/tag-namespaces.yaml`. No `phase.md`.

So `doctor` reports a finding, `doctor --repair` claims "Scaffolded missing desk/
structure", and the finding survives. It is unrepairable from inside a consuming
repo.

## Current state in this repo

Resolved incidentally: a `--repair` run did eventually create
`desk/rituals/phase.md`, and `deskops doctor` now reports
"Desk is healthy. No issues found." The upstream inconsistency remains.

## Goal

Fix in deskops: either add `phase.md` to the scaffold templates, or drop it from
the doctor's required set. Also worth noting that `phase.md` is listed in the
doctor's own `ignored_modeled_names`, so it is required to exist but explicitly not
modelled — which suggests the requirement is the accident.

## Scope

`/home/jp/proyectos/hum-ecosystem/tools/deskops/` — send via
`deskops inbox` to that repo rather than editing from here.

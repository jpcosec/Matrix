---
id: pill-05-void-marker
entity: void/∅ marker convention
status: implemented
---

## Why

YAML test data files use `∅` to represent "void" / "no value" / "false".
The usage is inconsistent — sometimes `∅` means `False`, sometimes it means
`None`, sometimes it's mixed with `false`/`null` in the same file.

## What

A Unicode symbol `∅` (U+2205, EMPTY SET) used in YAML fixture files as a
sentinel value.

## Where

Files with `∅` usage:
- `tests/test_serialization.py` — contains ∅ in test data strings
- Any `.yaml`/`.yml` fixture files in the repo

## How

### Current behavior in `serial.py`
The `Atom` class uses ∅ to signify an unset/void state during serialization.
The parser treats `∅` as a special symbol during YAML load.

### Standardization rule
Every ∅ instance must be **one** of:
- A Python `None` on the object side, serialized as `~` or `null` in YAML.
- A Python `False` on the object side, serialized as `false` in YAML.
- A special sentinel `Atom.VOID` (a dedicated singleton) if the distinction
  between `None` and "unset" matters.

Do NOT mix. Pick one meaning per ∅ usage site.

## How Not

- Do NOT have ∅ mean `None` in one place and `False` in another.
- Do NOT keep ∅ as a raw Unicode symbol in YAML — YAML has native `null`/`~`
  and `false`.
- Do NOT add new ∅ usage to YAML files.
- Do NOT confuse `∅` with `Atom` — ∅ is a serialization sentinel, Atom is
  a runtime value type.

## Why (depth)

∅ was borrowed from the mathematical empty-set symbol as a quick sentinel
during prototyping. It worked for ad-hoc test data but violates YAML
conventions and confuses readers. Standardizing to YAML-native values
removes a source of subtle bugs (e.g., ∅ round-tripping as a string when
the YAML loader doesn't recognize it).

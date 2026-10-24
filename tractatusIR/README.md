# Graphlang Prototype

This directory contains the executable `graphlang` prototype code and smoke tests.

## What Lives Here

- Common Lisp prototype runtime
- smoke tests
- temporary execution artifacts

## What Does Not Live Here

- current-state documentation
  - see `docs/architecture/graphlang/`
- active work notes and plans
  - see `desk/graphlang/`
- pending metamodel closures
  - see `desk/pendientes/`
- architectural decisions
  - see `desk/adrs/`

## Main Runtime Files

- `tractatus-core.lisp`
- `tractatus-periphery.lisp`
- `tractatus-semantics.lisp`
- `tractatus-worlds.lisp`
- `tractatus-ring.lisp`
- `tractatus-axes.lisp`
- `tractatus-discrimination.lisp`
- `tractatus-persistence.lisp`

## Main Smoke Tests

- `smoke-test.lisp`
- `world-smoke-test.lisp`
- `semantics-smoke-test.lisp`
- `ring-smoke-test.lisp`
- `axes-smoke-test.lisp`
- `discrimination-smoke-test.lisp`
- `persistence-smoke-test.lisp`

## Rule

The root of `graphlang/` should contain code, tests, and this `README.md` only.

## Setup

This is a **Common Lisp** prototype. You need a working Lisp implementation and **ASDF** (the system definition facility). Most Lisps bundle ASDF; install one if missing.

### Prerequisites

- A Common Lisp implementation (any of: **SBCL**, CCL, ECL, CLISP, ABCL)
- **ASDF 3.x** (bundled with most modern Lisps)

### Loading the System

The Lisp system is defined in `tractatusIR.asd` (or equivalent). To load from a REPL:

```lisp
;; 1. Push this directory onto ASDF's central registry
(push #p"/absolute/path/to/hum-ecosystem/tools/tractatusIR/" asdf:*central-registry*)

;; 2. Load the system
(asdf:load-system :graphlang)
```

Alternatively, configure ASDF via `~/.config/common-lisp/source-registry.conf.d/graphlang.conf`:

```common-lisp
(:directory "/absolute/path/to/hum-ecosystem/tools/tractatusIR/")
```

Then `(asdf:load-system :graphlang)` will work without manual registry pushing.

### Running the Smoke Tests

Load each `*-smoke-test.lisp` file directly in your REPL:

```lisp
(load "smoke-test.lisp")
(load "world-smoke-test.lisp")
(load "semantics-smoke-test.lisp")
;; ...etc
```

Or from the shell (SBCL example):

```bash
sbcl --load tractatus-core.lisp --load smoke-test.lisp --eval '(sb-ext:exit)'
```

## Notes

- No external dependencies beyond a standard Common Lisp distribution.
- The system targets portability across SBCL, CCL, and ECL.

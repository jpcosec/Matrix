# Test Directory

Test suite for the `lisp/` Tractatus IR implementation. Does **not** modify any files in `lisp/`.

## Structure
- `run-all-tests.lisp` - Master test runner
- `test-signatures.lisp` - Tests for `datype+operations/` (tractatus-signatures)
- `test-semantics.lisp` - Tests for `sin-mask+tractatus logic/` (tractatus-semantics)
- `test-discrimination.lisp` - Tests for `higher functions/` (tractatus-discrimination)
- `test-parser.lisp` - Tests for `encoding/` (tractatus-parser)
- `test-db.lisp` - Tests for `utils/` (tractatus-db)

## Running Tests
1. Load the Tractatus ASDF system first:
   ```lisp
   (asdf:load-system :tractatus)
   ```
2. Load and run all tests:
   ```lisp
   (load "test/run-all-tests.lisp")
   (run-all-tests:run-all-tests)
   ```

## Notes
- Tests use only exported symbols from `lisp/` packages
- No modifications to `lisp/` code
- Tests cover all major aspects: signatures, semantics, discrimination, parsing, persistence

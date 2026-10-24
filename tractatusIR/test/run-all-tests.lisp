;;; run-all-tests.lisp
;;; Master test runner for all tractatus lisp/ aspects
;;; Usage: Load tractatus system first, then (load "run-all-tests.lisp")

(defpackage :run-all-tests
  (:use :cl)
  (:export #:run-all-tests))

(in-package :run-all-tests)

(defun run-all-tests ()
  (format t "~%========================================~%")
  (format t "  TRACTATUS IR - ALL TESTS~%")
  (format t "========================================~%~%")
  (handler-case
      (progn
        (test-signatures:run-signature-tests)
        (test-semantics:run-semantics-tests)
        (test-discrimination:run-discrimination-tests)
        (test-parser:run-parser-tests)
        (test-db:run-db-tests)
        (format t "~%========================================~%")
        (format t "  ALL TESTS PASSED SUCCESSFULLY~%")
        (format t "========================================~%~%"))
    (error (e)
      (format t "~%TEST FAILED: ~A~%" e))))

;; To run: (run-all-tests)

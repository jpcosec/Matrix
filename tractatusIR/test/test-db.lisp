;;; test-db.lisp
;;; Tests for utils/tractatus-db
;;; Depends on: tractatus-signatures, tractatus-semantics, tractatus-discrimination,
;;;            tractatus-update, tractatus-selection, tractatus-security,
;;;            tractatus-inference, tractatus-versioning, tractatus-db

(defpackage :test-db
  (:use :cl :tractatus-db)
  (:export #:run-db-tests))

(in-package :test-db)

(defun test-save-load-all ()
  (format t "Test: Save and load all state... ")
  (let ((test-file "/tmp/tractatus-test-db.sexp"))
    ;; Clear first
    (clear-all)
    ;; Save empty state
    (save-all-to-file test-file)
    ;; Load back
    (load-all-from-file test-file)
    (format t "PASSED~%")
    (delete-file test-file)))

(defun test-print-status ()
  (format t "Test: Print status (no crash)... ")
  (print-status)
  (format t "PASSED~%")))

(defun run-db-tests ()
  (format t "~%=== Running DB Tests ===~%")
  (test-save-load-all)
  (test-print-status)
  (format t "=== All DB Tests Passed ===~%~%"))

;;; test-signatures.lisp
;;; Tests for datype+operations (tractatus-signatures)
;;; Depends on: tractatus-signatures package

(defpackage :test-signatures
  (:use :cl :tractatus-signatures)
  (:export #:run-signature-tests))

(in-package :test-signatures)

(defun test-concept-signature-creation ()
  (format t "Test: Concept signature creation... ")
  (let ((sig (make-concept-signature
               :bits '(1 0 1)
               :bit-dictionary '(:color :size :shape)
               :context-id :test-ctx
               :concept-id :car)))
    (assert (equal (concept-signature-bits sig) '(1 0 1)))
    (assert (eq (concept-signature-context-id sig) :test-ctx))
    (assert (eq (concept-signature-concept-id sig) :car))
    (format t "PASSED~%")))

(defun test-query-signature-creation ()
  (format t "Test: Query signature creation... ")
  (let ((sig (make-query-signature
               :bits '(0 1 0)
               :constraints '(:color :red)
               :context-id :test-ctx)))
    (assert (equal (query-signature-bits sig) '(0 1 0)))
    (assert (equal (query-signature-constraints sig) '(:color :red)))
    (format t "PASSED~%")))

(defun test-semantic-and ()
  (format t "Test: Semantic AND operation... ")
  (let* ((sig-a (make-concept-signature :bits '(1 0 1 0)))
         (sig-b (make-concept-signature :bits '(1 1 0 0)))
         (result (semantic-and sig-a sig-b)))
    (assert (logical-result-p result))
    (assert (eq (logical-result-status result) :sinnvoll))
    (format t "PASSED~%")))

(defun test-semantic-or ()
  (format t "Test: Semantic OR operation... ")
  (let* ((sig-a (make-concept-signature :bits '(1 0 1 0)))
         (sig-b (make-concept-signature :bits '(0 1 0 1)))
         (result (semantic-or sig-a sig-b)))
    (assert (logical-result-p result))
    (format t "PASSED~%")))

(defun test-contrast ()
  (format t "Test: Contrast operation... ")
  (let* ((sig-a (make-concept-signature :bits '(1 0 1) :concept-id :car))
         (sig-b (make-concept-signature :bits '(0 1 1) :concept-id :bike))
         (result (contrast sig-a sig-b)))
    (assert (contrast-signature-p result))
    (format t "PASSED~%")))

(defun run-signature-tests ()
  (format t "~%=== Running Signature Tests ===~%")
  (test-concept-signature-creation)
  (test-query-signature-creation)
  (test-semantic-and)
  (test-semantic-or)
  (test-contrast)
  (format t "=== All Signature Tests Passed ===~%~%"))

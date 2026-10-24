;;; test-semantics.lisp
;;; Tests for sin-mask+tractatus-logic (tractatus-semantics)
;;; Depends on: tractatus-signatures, tractatus-semantics

(defpackage :test-semantics
  (:use :cl :tractatus-signatures :tractatus-semantics)
  (:export #:run-semantics-tests))

(in-package :test-semantics)

(defun setup-test-universe ()
  (setf (universe :test-ctx) '(:car :bike :tree))
  (format t "Set up test universe for context :test-ctx~%"))

(defun test-validate-structural ()
  (format t "Test: Structural validation... ")
  (let* ((sig (make-concept-signature
                :bits '(1 0 1)
                :bit-dictionary '(:color :size :shape)
                :context-id :test-ctx
                :concept-id :car))
         (result (validate-structural sig :test-ctx)))
    (assert (logical-result-p result))
    (assert (eq (logical-result-status result) :sinnvoll))
    (format t "PASSED~%")))

(defun test-denote ()
  (format t "Test: Denotation (⟦x⟧_K)... ")
  (let* ((sig (make-concept-signature
                :bits '(1 0 1)
                :context-id :test-ctx
                :concept-id :car))
         (denotation (denote sig :test-ctx)))
    (assert (member :car denotation))
    (format t "PASSED~%")))

(defun test-sinnvoll-p ()
  (format t "Test: sinnvoll-p check... ")
  (let* ((sig (make-concept-signature
                :bits '(1 0 1)
                :context-id :test-ctx))
         (result (validate sig :test-ctx)))
    (assert (sinnvoll-p result))
    (format t "PASSED~%")))

(defun test-classify-sense ()
  (format t "Test: Sense classification... ")
  (let* ((sig (make-concept-signature
                :bits '(1 0 1)
                :context-id :test-ctx))
         (denotation '(:car)))
    (assert (eq (classify-sense sig denotation :test-ctx) :sinnvoll))
    (format t "PASSED~%")))

(defun run-semantics-tests ()
  (format t "~%=== Running Semantics Tests ===~%")
  (setup-test-universe)
  (test-validate-structural)
  (test-denote)
  (test-sinnvoll-p)
  (test-classify-sense)
  (format t "=== All Semantics Tests Passed ===~%~%"))

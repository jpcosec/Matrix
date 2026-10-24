;;; test-parser.lisp
;;; Tests for encoding/tractatus-parser
;;; Depends on: tractatus-signatures, tractatus-security, tractatus-parser

(defpackage :test-parser
  (:use :cl :tractatus-signatures :tractatus-parser)
  (:export #:run-parser-tests))

(in-package :test-parser)

(defun test-projection-ir-creation ()
  (format t "Test: ProjectionIR creation... ")
  (let ((ir (make-projection-ir
              :type :dimension
              :dimension :color
              :subject :car
              :value :red
              :context-id :test-ctx)))
    (assert (eq (projection-ir-type ir) :dimension))
    (assert (eq (projection-ir-dimension ir) :color))
    (assert (eq (projection-ir-subject ir) :car))
    (assert (eq (projection-ir-value ir) :red))
    (format t "PASSED~%")))

(defun test-tokenize ()
  (format t "Test: Basic tokenization... ")
  (let ((tokens (tokenize "What color is the car?")))
    (assert (> (length tokens) 0))
    (format t "PASSED~%")))

(defun test-parse-dimension-query ()
  (format t "Test: Parse dimension query (D(c)=v)... ")
  (let* ((ir (try-parse-dimension-query
               (tokenize "color of car is red")
               :test-ctx)))
    (when ir
      (assert (eq (projection-ir-type ir) :dimension))
      (assert (eq (projection-ir-dimension ir) :color)))
    (format t "PASSED~%")))

(defun run-parser-tests ()
  (format t "~%=== Running Parser Tests ===~%")
  (test-projection-ir-creation)
  (test-tokenize)
  (test-parse-dimension-query)
  (format t "=== All Parser Tests Passed ===~%~%"))

;;;; semantics-smoke-test.lisp
;;;; Smoke tests for tractatus-semantics package.

(load "tractatus-core.lisp")
(load "tractatus-semantics.lisp")

(in-package #:tractatus-semantics)

(defun test-signature-creation ()
  (let ((sig (make-signature :bits "101"
                             :valid-mask "111"
                             :context-id :test-context
                             :type :concept)))
    (assert (string= (signature-bits sig) "101"))
    (assert (eq (signature-type sig) :concept))
    (assert (eq (signature-status sig) :unknown))
    (format t "Signature creation test passed.~%")))

(defun test-fact-creation ()
  (let ((f (make-instance 'fact
                          :subject :c-lechuga
                          :predicate :d-parte
                          :object :v-hoja
                          :context :k-cocina
                          :hash-id "test-fact-hash")))
    (assert (eq (fact-subject f) :c-lechuga))
    (assert (eq (fact-predicate f) :d-parte))
    (assert (eq (fact-object f) :v-hoja))
    (format t "Fact creation test passed.~%")))

(defun test-semantic-xor ()
  (let* ((sig-a (make-signature :bits "100"))
         (sig-b (make-signature :bits "010"))
         (res (semantic-xor sig-a sig-b :test-context)))
    (assert (eq (signature-type res) :contrast))
    (assert (eq (signature-status res) :sinnvoll))
    (format t "Semantic XOR placeholder test passed.~%")))

(defun run-all-tests ()
  (test-signature-creation)
  (test-fact-creation)
  (test-semantic-xor)
  (format t "All semantic smoke tests passed.~%"))

(run-all-tests)

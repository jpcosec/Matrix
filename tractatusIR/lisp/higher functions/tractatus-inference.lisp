;;;; tractatus-inference.lisp
;;;; Inference engine: logical, heuristic, statistical, LLM inference
;;;; Implements Turn 44 item 7: inference rules

(defpackage :tractatus-inference
  (:use :cl :tractatus-signatures :tractatus-semantics)
  (:export
   #:defrule
   #:infer
   #:forward-chain
   #:backward-chain
   #:apply-rule
   #:rule-type
   #:logical-infer
   #:heuristic-infer
   #:clear-rules))

(in-package :tractatus-inference)

;;; ============================================================
;;; Rule Structures
;;; ============================================================

(defstruct inference-rule
  "An inference rule with when-conditions and then-consequences.
   From Turn 44: InferenceRule structure."
  (id nil :type symbol)
  (type :logical :type keyword)  ; :logical, :heuristic, :statistical, :llm
  (when-conditions nil :type list)
  (then-consequences nil :type list)
  (confidence 1.0 :type float)
  (description nil :type string))

(defvar *rules* (make-hash-table :test 'eq)
  "Maps rule-id to inference-rule")

(defvar *inference-log* nil
  "Log of inference steps for traceability")

;;; ============================================================
;;; Define Rule
;;; ============================================================

(defun defrule (id &key (type :logical) when then (confidence 1.0) (description ""))
  "Define a new inference rule.
   when: list of conditions ((relation/predicate args ...) ...)
   then: list of consequences ((relation/predicate args ...) ...)"
  (let ((rule (make-inference-rule
               :id id
               :type type
               :when-conditions when
               :then-consequences then
               :confidence (float confidence)
               :description description)))
    (setf (gethash id *rules*) rule)
    rule))

;;; ============================================================
;;; Main Inference Function
;;; ============================================================

(defun infer (facts context-id &key (type nil) (max-depth 10))
  "Run inference on facts in context.
   Returns list of inferred facts.
   type: nil (all), :logical, :heuristic, :statistical, :llm"
  (let ((applicable-rules (if type
                              (remove-if-not #'(lambda (r) (eq (inference-rule-type r) type))
                                              (loop for r being each hash-value of *rules* collect r))
                              (loop for r being each hash-value of *rules* collect r)))
        (inferred nil)
        (depth 0))
    (labels ((infer-step (current-facts)
               (when (>= depth max-depth)
                 (return-from infer-step nil))
               (incf depth)
               (dolist (rule applicable-rules)
                 (let ((new-facts (apply-rule rule current-facts context-id)))
                   (dolist (nf new-facts)
                     (unless (member nf inferred :test #'equal)
                       (push nf inferred)
                       (infer-step (cons nf current-facts))))))))
      (infer-step facts))
    inferred))

;;; ============================================================
;;; Apply Rule
;;; ============================================================

(defun apply-rule (rule facts context-id)
  "Apply a single rule to facts.
   Returns list of new facts inferred."
  (let ((when-conds (inference-rule-when-conditions rule))
        (then-cons (inference-rule-then-consequences rule))
        (new-facts nil))
    ;; Check if all when-conditions are satisfied
    (when (conditions-satisfied-p when-conds facts context-id)
      ;; Generate consequences
      (dolist (conseq then-cons)
        (let ((inferred (instantiate-consequence conseq facts)))
          (when inferred
            (push inferred new-facts)
            (push (list :rule (inference-rule-id rule)
                        :fact inferred
                        :type (inference-rule-type rule)
                        :confidence (inference-rule-confidence rule))
                  *inference-log*)))))
    new-facts))

(defun conditions-satisfied-p (conditions facts context-id)
  "Check if all conditions are satisfied by facts."
  (dolist (cond conditions t)
    (unless (or (member cond facts :test #'equal)
                (fact-exists-p cond facts context-id))
      (return nil))))

(defun fact-exists-p (pattern facts context-id)
  "Check if a fact matching pattern exists.
   Pattern: (predicate arg1 arg2 ...) with possible variables."
  (declare (ignore context-id))
  (dolist (fact facts t)
    (when (match-fact pattern fact)
      (return t))))

(defun match-fact (pattern fact)
  "Match a pattern against a fact.
   Variables start with ?."
  (when (and (listp pattern) (listp fact)
             (= (length pattern) (length fact)))
    (every #'(lambda (p f)
              (if (and (symbolp p) (char= (char (symbol-name p) 0) #\?))
                  t  ; variable matches anything
                  (equal p f)))
          pattern fact)))

(defun instantiate-consequence (conseq facts)
  "Instantiate consequence with bindings from facts."
  (declare (ignore facts))
  ;; Simple instantiation: just return as-is for now
  ;; Would need full unification
  conseq)

;;; ============================================================
;;; Forward and Backward Chaining
;;; ============================================================

(defun forward-chain (initial-facts context-id &key (type nil) (max-iterations 100))
  "Forward chaining: apply rules repeatedly until no new facts.
   Returns all derived facts."
  (let ((current-facts initial-facts)
        (new-facts t)
        (iterations 0))
    (loop while (and new-facts (< iterations max-iterations))
          do (setf new-facts (infer current-facts context-id :type type))
             (setf current-facts (append current-facts new-facts))
             (incf iterations))
    current-facts))

(defun backward-chain (goal facts context-id &key (type nil))
  "Backward chaining: find rules that can prove goal.
   Returns list of rules that support the goal."
  (declare (ignore facts context-id))
  (let ((supporting-rules nil))
    (maphash #'(lambda (id rule)
                (when (or (null type) (eq (inference-rule-type rule) type))
                  (dolist (conseq (inference-rule-then-consequences rule))
                    (when (equal conseq goal)
                      (push (list id rule) supporting-rules)))))
              *rules*)
    supporting-rules))

;;; ============================================================
;;; Typed Inference
;;; ============================================================

(defun logical-infer (facts context-id)
  "Run only logical inference rules (truth-preserving)."
  (infer facts context-id :type :logical))

(defun heuristic-infer (facts context-id)
  "Run heuristic inference (domain-specific patterns)."
  (infer facts context-id :type :heuristic))

(defun statistical-infer (facts context-id)
  "Run statistical inference (probability-based)."
  (infer facts context-id :type :statistical))

;;; ============================================================
;;; Rule Type Helpers
;;; ============================================================

(defun rule-type (rule-id)
  "Get type of a rule."
  (let ((rule (gethash rule-id *rules*)))
    (when rule
      (inference-rule-type rule))))

;;; ============================================================
;;; Clear Rules
;;; ============================================================

(defun clear-rules ()
  "Clear all inference rules."
  (clrhash *rules*)
  (setf *inference-log* nil)
  t)

;;; ============================================================
;;; Example Rules (from Turn 44)
;;; ============================================================

#|
;; Define web capability inference rule
(defrule 'R_WEB_CAPABILITY
  :type :logical
  :when '((imports PROJECT x) (D_LIBRARY_ROLE x web_framework))
  :then '((uses_capability PROJECT web_api))
  :description "If project imports a web framework, it uses web API capability")

;; Define same bucket inference rule
(defrule 'R_SAME_BUCKET
  :type :logical
  :when '((D_PARTE_COMESTIBLE a hoja) (D_PARTE_COMESTIBLE b hoja))
  :then '((same_bucket a b D_PARTE_COMESTIBLE.hoja))
  :description "If two concepts share same dimension value, they are in same bucket")

;; Run inference
(let ((facts '((imports MY_PROJECT LIB_FASTAPI)
               (D_LIBRARY_ROLE LIB_FASTAPI web_framework))))
  (logical-infer facts 'K_SOFTWARE_ANALYSIS))
|#

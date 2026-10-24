;;;; tractatus-semantics.lisp
;;;; Semantic runtime: validate, denote, status, sense classification
;;;; Implements Tractarian core: sinnvoll/sinnlos/unsinnig

(defpackage :tractatus-semantics
  (:use :cl :tractatus-signatures)
  (:export
   #:validate
   #:denote
   #:status
   #:sinnvoll-p
   #:sinnlos-p
   #:unsinnig-p
   #:classify-sense))

(in-package :tractatus-semantics)

;;; ============================================================
;;; Universe and Context Management
;;; ============================================================

(defvar *universes* (make-hash-table :test 'eq)
  "Maps context-id to local universe U (list of concept-ids)")

(defun universe (context-id)
  (gethash context-id *universes*))

(defun (setf universe) (concepts context-id)
  (setf (gethash context-id *universes*) concepts))

;;; ============================================================
;;; Validate: Full Validation (Structural + Sense)
;;; Corresponds to: validate + denote + classify
;;; ============================================================

(defun validate (sig context-id)
  "Full validation: structural + sense check.
   Returns LogicalResult with status."
  (let ((struct-result (validate-structural sig context-id)))
    (unless (eq (logical-result-status struct-result) :sinnvoll)
      (return-from validate struct-result))
    ;; If structurally valid, check sense
    (let ((denotation (denote sig context-id)))
      (classify-sense sig denotation context-id))))

;;; ============================================================
;;; Denote: ⟦x⟧_K ⊆ U
;;; Returns subset of universe satisfying the signature
;;; ============================================================

(defun denote (sig context-id)
  "⟦x⟧_K ⊆ U
   Returns list of concept-ids in universe that satisfy the signature.
   Implements:
     ⟦x AND y⟧_K = ⟦x⟧_K ∩ ⟦y⟧_K
     ⟦x OR y⟧_K  = ⟦x⟧_K ∪ ⟦y⟧_K
     ⟦NOT x⟧_K   = U \ ⟦x⟧_K"
  (let ((bits (slot-value sig 'bits))
        (bit-dict (slot-value sig 'bit-dictionary))
        (u (universe context-id)))
    (unless u
      (return-from denote nil))
    ;; Filter universe: keep concepts whose signature matches bits
    (labels ((matches-p (concept-sig)
               (let ((c-bits (slot-value concept-sig 'bits)))
                 (every #'(lambda (b cb) (or (= b 1) (= cb b)))
                        bits c-bits))))
      (remove-if-not #'matches-p u))))

;;; ============================================================
;;; Status: Tractarian Sense Classification
;;; Implements the Wittgensteinian boundary of sense
;;; ============================================================

(defun status (sig context-id)
  "Classify signature into Tractarian sense categories.
   Returns: :sinnvoll, :sinnlos-tautology, :sinnlos-contradiction, :unsinnig"
  (let ((validation-result (validate sig context-id)))
    (logical-result-status validation-result)))

(defun classify-sense (sig denotation context-id)
  "Classify based on denotation size relative to universe.
   Implements:
     sinnvoll(x,K)  ⇔ 0 < |⟦x⟧_K| < |U|
     sinnlos_taut(x,K) ⇔ ⟦x⟧_K = U
     sinnlos_contra(x,K) ⇔ ⟦x⟧_K = ∅
     unsinnig(x,K) ⇔ x ∉ WF_K"
  (let ((u (universe context-id))
        (structural-result (validate-structural sig context-id)))
    ;; First check structural validity
    (unless (eq (logical-result-status structural-result) :sinnvoll)
      (return-from classify-sense structural-result))
    ;; Now classify based on denotation
    (cond
      ((null denotation)
       (make-logical-result
        :signature sig
        :status :sinnlos-contradiction
        :denotation nil
        :reason "Denotation is empty (⟦x⟧_K = ∅)"))
      ((= (length denotation) (length u))
       (make-logical-result
        :signature sig
        :status :sinnlos-tautology
        :denotation denotation
        :reason "Denotation equals universe (⟦x⟧_K = U)"))
      (t
       (make-logical-result
        :signature sig
        :status :sinnvoll
        :denotation denotation
        :reason "0 < |⟦x⟧_K| < |U|")))))

;;; ============================================================
;;; Sense Predicates
;;; ============================================================

(defun sinnvoll-p (sig context-id)
  "Check if signature is meaningful (sinnvoll).
   sinnvoll(x,K) ⇔ 0 < |⟦x⟧_K| < |U|"
  (let ((result (status sig context-id)))
    (eq result :sinnvoll)))

(defun sinnlos-p (sig context-id)
  "Check if signature is senseless (sinnlos).
   Includes both tautologies and contradictions."
  (let ((result (status sig context-id)))
    (or (eq result :sinnlos-tautology)
        (eq result :sinnlos-contradiction))))

(defun unsinnig-p (sig context-id)
  "Check if signature is nonsensical (unsinnig).
   unsinnig(x,K) ⇔ x ∉ WF_K"
  (let ((result (status sig context-id)))
    (eq result :unsinnig)))

;;; ============================================================
;;; Explain: Verbalize Semantic Result
;;; ============================================================

(defun explain (logical-result)
  "Generate human-readable explanation of a LogicalResult."
  (let ((status (logical-result-status logical-result))
        (reason (logical-result-reason logical-result))
        (sig (logical-result-signature logical-result))
        (denotation (logical-result-denotation logical-result)))
    (format nil "Status: ~a~%Reason: ~a~%Signature: ~a~%Denotation size: ~a~%"
            status reason sig (length denotation))))

;;; ============================================================
;;; Refine: Collision Resolution
;;; ============================================================

(defun refine (sig1 sig2 context-id &key (dimension nil))
  "Refine two concepts that collide (same signature).
   Returns new signature with added dimension."
  (if dimension
      ;; Add specific dimension to break collision
      (let ((new-bits (append (slot-value sig1 'bits)
                              (list (if (eq (slot-value sig1 'concept-id)
                                            (slot-value sig2 'concept-id))
                                      1 0)))))
        (make-concept-sig (slot-value sig1 'concept-id)
                          context-id
                          new-bits
                          (append (slot-value sig1 'bit-dictionary)
                                  (list dimension))))
      ;; Default: return contrast
      (contrast sig1 sig2 context-id)))

;;; ============================================================
;;; Example Usage (commented out)
;;; ============================================================

#|
;; Setup a simple context
(setf (universe 'K_COCINA) '(C_LECHUGA C_ZANAHORIA C_APIO))
(setf (valid-mask 'K_COCINA)
      (make-mask 'K_COCINA :valid '(1 1 1)
                 '((0 . hoja_comestible) (1 . raiz_comestible) (2 . tallo_comestible))))
(setf (sense-mask 'K_COCINA)
      (make-mask 'K_COCINA :sense '(1 1 1)
                 '((0 . hoja_comestible) (1 . raiz_comestible) (2 . tallo_comestible))))
(setf (discriminative-mask 'K_COCINA)
      (make-mask 'K_COCINA :discriminative '(1 1 1)
                 '((0 . hoja_comestible) (1 . raiz_comestible) (2 . tallo_comestible))))
(setf (observed-mask 'K_COCINA)
      (make-mask 'K_COCINA :observed '(1 1 1)
                 '((0 . hoja_comestible) (1 . raiz_comestible) (2 . tallo_comestible))))

;; Create a concept signature for lechuga
(defparameter *lechuga-sig*
  (make-concept-sig 'C_LECHUGA 'K_COCINA
                    '(1 0 0)
                    '((0 . hoja_comestible) (1 . raiz_comestible) (2 . tallo_comestible))))

;; Validate and get status
(status *lechuga-sig* 'K_COCINA)
;; => :SINNVOLL

;; Denote
(denote *lechuga-sig* 'K_COCINA)
;; => list of concepts matching [1,0,0]

;; Explain
(explain (validate *lechuga-sig* 'K_COCINA))
|#

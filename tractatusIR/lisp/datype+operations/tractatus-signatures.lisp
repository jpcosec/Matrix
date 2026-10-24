;;;; tractatus-signatures.lisp
;;;; Base signature types, masks, and typed bitwise operations
;;;; Implements the mathematical formalization from specs/formalization/mathematical_formalization.md

(defpackage :tractatus-signatures
  (:use :cl)
  (:export
   ;; Signature types
   #:concept-signature
   #:query-signature
   #:contrast-signature
   #:mask-signature
   #:logical-result
   ;; Mask accessors
   #:valid-mask
   #:sense-mask
   #:discriminative-mask
   #:observed-mask
   #:effective-mask
   ;; Operations
   #:semantic-and
   #:semantic-or
   #:semantic-not
   #:contrast
   #:validate-structural
   #:make-logical-result))

(in-package :tractatus-signatures)

;;; ============================================================
;;; Signature Types (Section 15 of mathematical formalization)
;;; ============================================================

(defstruct concept-signature
  "A concept's binary signature under a specific context.
   Corresponds to ConceptSignature in the formal notation."
  (bits nil :type list :read-only nil)
  (bit-dictionary nil :type list :read-only nil)
  (context-id nil :type symbol :read-only nil)
  (concept-id nil :type symbol :read-only nil))

(defstruct query-signature
  "A query as typed binary signature with constraints.
   Corresponds to QuerySignature: D=v, Q1 ∧ Q2, etc."
  (bits nil :type list :read-only nil)
  (bit-dictionary nil :type list :read-only nil)
  (context-id nil :type symbol :read-only nil)
  (constraints nil :type list :read-only nil))

(defstruct contrast-signature
  "A contrast between two concepts as XOR of their signatures.
   Corresponds to ContrastSignature: D(c1) ≠ D(c2)."
  (bits nil :type list :read-only nil)
  (bit-dictionary nil :type list :read-only nil)
  (context-id nil :type symbol :read-only nil)
  (concept-1 nil :type symbol :read-only nil)
  (concept-2 nil :type symbol :read-only nil))

(defstruct mask-signature
  "A mask selecting valid/meaningful bits in a context.
   Corresponds to the 4 masks: valid, sense, discriminative, observed."
  (bits nil :type list :read-only nil)
  (bit-dictionary nil :type list :read-only nil)
  (mask-type nil :type keyword :read-only nil)
  (context-id nil :type symbol :read-only nil))

;;; ============================================================
;;; Logical Result (Tractatus core: sinnvoll/sinnlos/unsinnig)
;;; ============================================================

(defstruct logical-result
  "Result of a semantic operation with status classification.
   Implements the Tractarian sense boundary."
  (signature nil :type (or concept-signature query-signature contrast-signature) :read-only nil)
  (status nil :type keyword :read-only nil)
  (denotation nil :type list :read-only nil)
  (reason nil :type string :read-only nil))

;;; ============================================================
;;; Mask Structures (4 masks from mathematical formalization)
;;; ============================================================

(defvar *valid-masks* (make-hash-table :test 'eq)
  "valid_mask: what applies to concept (ontological)")

(defvar *sense-masks* (make-hash-table :test 'eq)
  "sense_mask: what has sense in context/task")

(defvar *discriminative-masks* (make-hash-table :test 'eq)
  "discriminative_mask: what separates candidates now")

(defvar *observed-masks* (make-hash-table :test 'eq)
  "observed_mask: what has been measured")

(defun valid-mask (context-id)
  (gethash context-id *valid-masks*))

(defun (setf valid-mask) (mask context-id)
  (setf (gethash context-id *valid-masks*) mask))

(defun sense-mask (context-id)
  (gethash context-id *sense-masks*))

(defun (setf sense-mask) (mask context-id)
  (setf (gethash context-id *sense-masks*) mask))

(defun discriminative-mask (context-id)
  (gethash context-id *discriminative-masks*))

(defun (setf discriminative-mask) (mask context-id)
  (setf (gethash context-id *discriminative-masks*) mask))

(defun observed-mask (context-id)
  (gethash context-id *observed-masks*))

(defun (setf observed-mask) (mask context-id)
  (setf (gethash context-id *observed-masks*) mask))

;;; ============================================================
;;; Effective Mask Computation
;;; m = valid AND sense AND discriminative AND observed
;;; ============================================================

(defun effective-mask (context-id)
  "Compute effective mask: m = valid ∧ sense ∧ discriminative ∧ observed"
  (let ((valid (valid-mask context-id))
        (sense (sense-mask context-id))
        (discriminative (discriminative-mask context-id))
        (observed (observed-mask context-id)))
    (unless (and valid sense discriminative observed)
      (return-from effective-mask nil))
    (make-mask-signature
     :bits (mapcar #'(lambda (v s d o)
                      (logand (logand v s) (logand d o)))
                  (mask-signature-bits valid)
                  (mask-signature-bits sense)
                  (mask-signature-bits discriminative)
                  (mask-signature-bits observed))
     :bit-dictionary (mask-signature-bit-dictionary valid)
     :mask-type :effective
     :context-id context-id)))

;;; ============================================================
;;; Typed Bitwise Operations
;;; ============================================================

(defun semantic-and (sig1 sig2 context-id)
  "semantic_and: Query × Query → Query
   ⟦x AND y⟧_K = ⟦x⟧_K ∩ ⟦y⟧_K"
  (let ((mask (effective-mask context-id)))
    (unless mask
      (return-from semantic-and
        (make-logical-result
         :signature sig1
         :status :unsinnig
         :reason "No effective mask available")))
    (make-query-signature
     :bits (mapcar #'(lambda (b1 b2 m)
                      (logand (logand b1 b2) m))
                  (slot-value sig1 'bits)
                  (slot-value sig2 'bits)
                  (mask-signature-bits mask))
     :bit-dictionary (slot-value sig1 'bit-dictionary)
     :context-id context-id
     :constraints (append (slot-value sig1 'constraints)
                          (slot-value sig2 'constraints)))))

(defun semantic-or (sig1 sig2 context-id)
  "semantic_or: Query × Query → Query
   ⟦x OR y⟧_K = ⟦x⟧_K ∪ ⟦y⟧_K"
  (let ((mask (effective-mask context-id)))
    (unless mask
      (return-from semantic-or
        (make-logical-result
         :signature sig1
         :status :unsinnig
         :reason "No effective mask available")))
    (make-query-signature
     :bits (mapcar #'(lambda (b1 b2 m)
                      (logand (logior b1 b2) m))
                  (slot-value sig1 'bits)
                  (slot-value sig2 'bits)
                  (mask-signature-bits mask))
     :bit-dictionary (slot-value sig1 'bit-dictionary)
     :context-id context-id
     :constraints (append (slot-value sig1 'constraints)
                          (slot-value sig2 'constraints)))))

(defun semantic-not (sig context-id)
  "semantic_not: Query → Query
   ⟦NOT x⟧_K = U \ ⟦x⟧_K"
  (let ((mask (effective-mask context-id)))
    (unless mask
      (return-from semantic-not
        (make-logical-result
         :signature sig
         :status :unsinnig
         :reason "No effective mask available")))
    (make-query-signature
     :bits (mapcar #'(lambda (b m)
                      (logand (logxor b 1) m))
                  (slot-value sig 'bits)
                  (mask-signature-bits mask))
     :bit-dictionary (slot-value sig 'bit-dictionary)
     :context-id context-id
     :constraints (slot-value sig 'constraints))))

(defun contrast (sig1 sig2 context-id)
  "contrast: Concept × Concept → Contrast
   diff(a, b) = a XOR b"
  (let ((mask (effective-mask context-id)))
    (unless mask
      (return-from contrast
        (make-logical-result
         :signature sig1
         :status :unsinnig
         :reason "No effective mask available")))
    (make-contrast-signature
     :bits (mapcar #'(lambda (b1 b2 m)
                      (logand (logxor b1 b2) m))
                  (slot-value sig1 'bits)
                  (slot-value sig2 'bits)
                  (mask-signature-bits mask))
     :bit-dictionary (slot-value sig1 'bit-dictionary)
     :context-id context-id
     :concept-1 (slot-value sig1 'concept-id)
     :concept-2 (slot-value sig2 'concept-id))))

;;; ============================================================
;;; Minimal Structural Validation
;;; Checks WF_K membership (well-formed signatures)
;;; ============================================================

(defun validate-structural (sig context-id)
  "Validate that signature belongs to WF_K (well-formed signatures).
   Checks: one-hot correctness, type correctness, dimension applicability."
  (let ((bits (slot-value sig 'bits))
        (bit-dict (slot-value sig 'bit-dictionary))
        (mask (effective-mask context-id)))
    (unless mask
      (return-from validate-structural
        (make-logical-result
         :signature sig
         :status :unsinnig
         :reason "No effective mask for validation")))
    (let ((effective-bits (mapcar #'(lambda (b m) (logand b m))
                                 bits (mask-signature-bits mask))))
      ;; Check: all bits are 0 or 1
      (unless (every #'(lambda (b) (or (= b 0) (= b 1))) effective-bits)
        (return-from validate-structural
          (make-logical-result
           :signature sig
           :status :unsinnig
           :reason "Invalid bit value (not 0 or 1)")))
      ;; Check: bits apply to context (valid_mask)
      (let ((valid (valid-mask context-id)))
        (unless valid
          (return-from validate-structural
            (make-logical-result
             :signature sig
             :status :unsinnig
             :reason "No valid mask for context")))
        (when (every #'= effective-bits (mask-signature-bits valid))
          (return-from validate-structural
            (make-logical-result
             :signature sig
             :status :sinnlos-tautology
             :reason "Signature equals valid mask (tautology)"))))
      ;; Default: sinnvoll if we got here
      (make-logical-result
       :signature sig
       :status :sinnvoll
       :denotation effective-bits))))

;;; ============================================================
;;; Constructor Helpers
;;; ============================================================

(defun make-logical-result (&key signature status denotation reason)
  (make-instance 'logical-result
                  :signature signature
                  :status status
                  :denotation denotation
                  :reason reason))

(defun make-concept-sig (concept-id context-id bits bit-dict)
  (make-concept-signature
   :concept-id concept-id
   :context-id context-id
   :bits bits
   :bit-dictionary bit-dict))

(defun make-query-sig (context-id bits bit-dict &optional constraints)
  (make-query-signature
   :context-id context-id
   :bits bits
   :bit-dictionary bit-dict
   :constraints (or constraints '())))

(defun make-contrast-sig (c1 c2 context-id bits bit-dict)
  (make-contrast-signature
   :concept-1 c1
   :concept-2 c2
   :context-id context-id
   :bits bits
   :bit-dictionary bit-dict))

(defun make-mask (context-id mask-type bits bit-dict)
  (make-mask-signature
   :context-id context-id
   :mask-type mask-type
   :bits bits
   :bit-dictionary bit-dict))

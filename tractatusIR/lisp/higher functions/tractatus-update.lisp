;;;; tractatus-update.lisp
;;;; Update operations: add/retract facts, rebuild signatures, detect collisions
;;;; Implements Turn 44 item 8: update operations for a living system

(defpackage :tractatus-update
  (:use :cl :tractatus-signatures :tractatus-semantics :tractatus-discrimination)
  (:export
   #:add-concept
   #:merge-concepts
   #:add-dimension
   #:add-value
   #:add-fact
   #:retract-fact
   #:update-context
   #:rebuild-signature
   #:recompute-matrices
   #:update-indices
   #:detect-collisions
   #:refine-collision
   #:materialize-derived-relations))

(in-package :tractatus-update)

;;; ============================================================
;;; Global State
;;; ============================================================

(defvar *concepts* (make-hash-table :test 'eq)
  "Maps concept-id to concept-signature")

(defvar *facts* (make-hash-table :test 'eq)
  "Maps fact-id to fact plist: (:expression :truth-status :epistemic-status :semantic-status :evidence)")

(defvar *dimensions* (make-hash-table :test 'eq)
  "Maps dimension-id to dimension plist: (:values :functional :cardinality :applies-to)")

(defvar *contexts* (make-hash-table :test 'eq)
  "Maps context-id to context plist")

(defvar *indices* (make-hash-table :test 'equal)
  "Signature index: maps context-id to hash-table of (signature-string . concepts)")

(defvar *fact-counter* 0)
(defvar *concept-counter* 0)

;;; ============================================================
;;; Add Concept
;;; ============================================================

(defun add-concept (label &key (context-id nil))
  "Add a new concept to the system.
   Returns concept-id."
  (incf *concept-counter*)
  (let ((concept-id (intern (format nil "C_~a" label))))
    (setf (gethash concept-id *concepts*) nil)
    (when context-id
      (push concept-id (gethash context-id *contexts*)))
    concept-id))

;;; ============================================================
;;; Merge Concepts
;;; ============================================================

(defun merge-concepts (c1 c2 &key (primary c1))
  "Merge two concepts. Primary keeps the identity.
   Transfers all facts and projections from c2 to primary."
  (let ((facts1 (gethash c1 *facts*))
        (facts2 (gethash c2 *facts*)))
    (setf (gethash primary *facts*) (append facts1 facts2))
    (remhash c2 *facts*)
    primary))

;;; ============================================================
;;; Add Dimension
;;; ============================================================

(defun add-dimension (dim-id values &key (functional :exactly-one) (applies-to nil))
  "Add a new dimension with its possible values.
   functional: :exactly-one, :zero-or-one, :many"
  (setf (gethash dim-id *dimensions*)
        (list :values values
              :functional functional
              :applies-to applies-to))
  dim-id)

;;; ============================================================
;;; Add Value to Dimension
;;; ============================================================

(defun add-value (dim-id value)
  "Add a new value to an existing dimension."
  (let ((dim (gethash dim-id *dimensions*)))
    (unless dim
      (error "Dimension ~a not found" dim-id))
    (let ((values (getf dim :values)))
      (unless (member value values)
        (setf (getf dim :values) (cons value values)))
      (setf (gethash dim-id *dimensions*) dim))))

;;; ============================================================
;;; Add Fact
;;; Implements Turn 44: add_fact algorithm
;;; ============================================================

(defun add-fact (expression &key (truth-status :asserted-true)
                                    (epistemic-status :observed)
                                    (evidence nil)
                                    (context-id nil))
  "Add a fact to the system.
   Implements: validate → store → update signature → update matrix → update indices → detect collisions"
  (incf *fact-counter*)
  (let ((fact-id (intern (format nil "F_~a" *fact-counter*))))
    ;; 1. Validate fact
    (let ((validation-result (validate-fact expression context-id)))
      (when (eq (getf validation-result :status) :unsinnig)
        (return-from add-fact
          (values nil (getf validation-result :reason)))))
    ;; 2. Store fact
    (setf (gethash fact-id *facts*)
          (list :expression expression
                :truth-status truth-status
                :epistemic-status epistemic-status
                :semantic-status (classify-fact expression context-id)
                :evidence evidence
                :context-id context-id))
    ;; 3. Update signature for subject
    (let ((subject (extract-subject expression)))
      (when subject
        (rebuild-signature subject context-id)))
    ;; 4. Update matrix for dimension
    (let ((dim (extract-dimension expression)))
      (when dim
        (recompute-matrices dim context-id)))
    ;; 5. Update indices
    (update-indices context-id)
    ;; 6. Detect collisions
    (detect-collisions context-id)
    fact-id))

(defun validate-fact (expression context-id)
  "Validate that fact expression is well-formed."
  (let ((dim (extract-dimension expression))
        (subject (extract-subject expression))
        (value (extract-value expression)))
    (unless dim
      (return-from validate-fact (list :status :unsinnig :reason "No dimension in expression")))
    (unless subject
      (return-from validate-fact (list :status :unsinnig :reason "No subject in expression")))
    (unless value
      (return-from validate-fact (list :status :unsinnig :reason "No value in expression")))
    ;; Check dimension exists
    (unless (gethash dim *dimensions*)
      (return-from validate-fact (list :status :unsinnig :reason (format nil "Unknown dimension ~a" dim))))
    ;; Check value is valid for dimension
    (let* ((dim-data (gethash dim *dimensions*))
           (valid-values (getf dim-data :values)))
      (unless (member value valid-values)
        (return-from validate-fact (list :status :unsinnig :reason (format nil "Invalid value ~a for dimension ~a" value dim)))))
    (list :status :sinnvoll :reason "Fact is well-formed")))

(defun classify-fact (expression context-id)
  "Classify fact's semantic status."
  (declare (ignore expression context-id))
  :sinnvoll)

(defun extract-subject (expression)
  "Extract subject concept from fact expression."
  (when (and (listp expression) (>= (length expression) 3))
    (second expression)))

(defun extract-dimension (expression)
  "Extract dimension from fact expression."
  (when (and (listp expression) (>= (length expression) 3))
    (first expression)))

(defun extract-value (expression)
  "Extract value from fact expression."
  (when (and (listp expression) (>= (length expression) 3))
    (third expression)))

;;; ============================================================
;;; Retract Fact
;;; ============================================================

(defun retract-fact (fact-id &key (reason "Manual retraction"))
  "Retract a fact from the system."
  (let ((fact (gethash fact-id *facts*)))
    (unless fact
      (return-from retract-fact nil))
    (setf (getf fact :truth-status) :asserted-false)
    (setf (getf fact :epistemic-status) :disputed)
    (setf (getf fact :reason) reason)
    (setf (gethash fact-id *facts*) fact)
    ;; Rebuild affected signatures
    (let ((subject (extract-subject (getf fact :expression))))
      (when subject
        (rebuild-signature subject (getf fact :context-id))))
    fact-id))

;;; ============================================================
;;; Update Context
;;; ============================================================

(defun update-context (context-id &key (add-dimensions nil) (remove-dimensions nil))
  "Update a context: add or remove dimensions."
  (let ((ctx (gethash context-id *contexts*)))
    (unless ctx
      (setf ctx (list :dimensions nil :universe nil)))
    (dolist (dim add-dimensions)
      (pushnew dim (getf ctx :dimensions)))
    (dolist (dim remove-dimensions)
      (setf (getf ctx :dimensions) (remove dim (getf ctx :dimensions))))
    (setf (gethash context-id *contexts*) ctx)
    (update-indices context-id)
    context-id))

;;; ============================================================
;;; Rebuild Signature
;;; ============================================================

(defun rebuild-signature (concept-id context-id)
  "Rebuild a concept's signature in context after fact changes."
  (let ((facts (loop for fact-id being each hash-key of *facts*
                          using (hash-value fact)
                          when (and (equal (getf fact :context-id) context-id)
                                     (equal (extract-subject (getf fact :expression)) concept-id))
                          collect fact)))
    (when facts
      ;; Recompute bits from facts
      (let ((new-bits (compute-bits-from-facts concept-id facts context-id)))
        (setf (gethash concept-id *concepts*)
              (make-concept-sig concept-id context-id new-bits nil)))))
  concept-id)

(defun compute-bits-from-facts (concept-id facts context-id)
  "Compute signature bits from facts about a concept."
  (declare (ignore concept-id context-id))
  (let ((bits nil))
    (dolist (fact facts)
      (let* ((expr (getf fact :expression))
             (dim (extract-dimension expr))
             (val (extract-value expr)))
        (when (and dim val)
          (push (list dim val) bits))))
    bits))

;;; ============================================================
;;; Recompute Matrices
;;; ============================================================

(defun recompute-matrices (dim-id context-id)
  "Recompute M1 and M1ᵀ after fact changes."
  (declare (ignore dim-id context-id))
  ;; Placeholder: would rebuild matrix from current facts
  t)

;;; ============================================================
;;; Update Indices
;;; ============================================================

(defun update-indices (&optional (context-id nil))
  "Update signature indices for context (or all contexts)."
  (if context-id
      (update-index-for-context context-id)
      (loop for ctx being each hash-key of *contexts*
            do (update-index-for-context ctx))))

(defun update-index-for-context (context-id)
  "Update signature index for a specific context."
  (let ((idx (make-hash-table :test 'equal)))
    (loop for concept-id being each hash-key of *concepts*
          do (let ((sig (gethash concept-id *concepts*)))
               (when (and sig (equal (slot-value sig 'context-id) context-id))
                 (let ((sig-str (format nil "~a" (slot-value sig 'bits))))
                   (push concept-id (gethash sig-str idx))))))
    (setf (gethash context-id *indices*) idx)))

;;; ============================================================
;;; Detect Collisions
;;; ============================================================

(defun detect-collisions (&optional (context-id nil))
  "Detect signature collisions in index.
   Returns list of (signature-string concept1 concept2 ...)."
  (let ((collisions nil))
    (if context-id
        (let ((idx (gethash context-id *indices*)))
          (when idx
            (maphash #'(lambda (sig-str concepts)
                         (when (> (length concepts) 1)
                           (push (cons sig-str concepts) collisions)))
                     idx)))
        (loop for ctx being each hash-key of *indices*
              do (maphash #'(lambda (sig-str concepts)
                              (when (> (length concepts) 1)
                                (push (cons sig-str concepts) collisions)))
                          (gethash ctx *indices*))))
    collisions))

;;; ============================================================
;;; Refine Collision
;;; ============================================================

(defun refine-collision (sig-str concepts context-id &key (new-dimension nil))
  "Refine a collision by adding a new dimension."
  (if new-dimension
      (progn
        (add-dimension new-dimension nil :functional :exactly-one)
        (dolist (c concepts)
          (rebuild-signature c context-id))
        (update-indices context-id)
        (detect-collisions context-id))
      (format t "Collision ~a between ~a needs dimension expansion~%" sig-str concepts)))

;;; ============================================================
;;; Materialize Derived Relations
;;; ============================================================

(defun materialize-derived-relations (&optional (context-id nil))
  "Materialize facts derived from inference rules.
   Placeholder for Turn 44 item 7."
  (declare (ignore context-id))
  (format t "Derived relations materialization not yet implemented~%"))

;;; ============================================================
;;; Example Usage (commented out)
;;; ============================================================

#|
;; Setup
(add-dimension 'D_PARTE_COMESTIBLE '(hoja raiz tallo) :functional :exactly-one)

;; Add facts
(add-fact '(D_PARTE_COMESTIBLE C_LECHUGA hoja)
          :context-id 'K_COCINA)
(add-fact '(D_PARTE_COMESTIBLE C_ESPINACA hoja)
          :context-id 'K_COCINA)

;; Detect collisions
(detect-collisions 'K_COCINA)
;; => ((" (1 0 0) " C_LECHUGA C_ESPINACA))

;; Refine
(refine-collision "(1 0 0)" '(C_LECHUGA C_ESPINACA) 'K_COCINA
                  :new-dimension 'D_ESTRUCTURA_HOJA)
|#

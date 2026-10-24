;;;; tractatus-security.lisp
;;;; Pseudo-proposition security: taxonomy of parsing/projection failures
;;;; Implements Turn 44 item 14: ensure robust parser against malformed input

(defpackage :tractatus-security
  (:use :cl :tractatus-signatures :tractatus-semantics)
  (:export
   #:security-check
   #:classify-error
   #:unknown-concept
   #:unknown-dimension
   #:unknown-value
   #:type-mismatch
   #:dimension-not-applicable
   #:outside-sense-mask
   #:malformed-signature
   #:no-denotation
   #:tautological-query
   #:ambiguous-reference
   #:valid-concept-p
   #:valid-dimension-p
   #:valid-value-p
   #:valid-type-p))

(in-package :tractatus-security)

;;; ============================================================
;;; Error Taxonomy (from Turn 44)
;;; ============================================================

(defparameter *error-types*
  '(:unknown-concept
    :unknown-dimension
    :unknown-value
    :type-mismatch
    :dimension-not-applicable
    :outside-sense-mask
    :malformed-signature
    :no-denotation
    :tautological-query
    :ambiguous-reference)
  "Complete taxonomy of parsing/projection failures.
   From Turn 44: UNKNOWN_CONCEPT, UNKNOWN_DIMENSION, etc.")

;;; ============================================================
;;; Security Check: Validate Expression Before Processing
;;; Implements: parser robustness for pseudo-propositions
;;; ============================================================

(defun security-check (expression context-id)
  "Comprehensive security check for an expression.
   Returns (values status reason) where status is :ok or error keyword."
  (cond
    ((null expression)
     (values :malformed-signature "Empty expression"))
    ((not (listp expression))
     (values :malformed-signature "Expression must be a list"))
    ((< (length expression) 3)
     (values :malformed-signature "Expression too short: needs (dim subject value)"))
    (t
     (let ((dim (first expression))
           (subject (second expression))
           (value (third expression)))
       ;; Check concept
       (multiple-value-bind (status reason) (check-concept subject context-id)
         (unless (eq status :ok)
           (return-from security-check (values status reason))))
       ;; Check dimension
       (multiple-value-bind (status reason) (check-dimension dim context-id)
         (unless (eq status :ok)
           (return-from security-check (values status reason))))
       ;; Check value
       (multiple-value-bind (status reason) (check-value dim value)
         (unless (eq status :ok)
           (return-from security-check (values status reason))))
       ;; Check type compatibility
       (multiple-value-bind (status reason) (check-type-compatibility dim subject value)
         (unless (eq status :ok)
           (return-from security-check (values status reason))))
       ;; Check sense mask
       (multiple-value-bind (status reason) (check-sense-mask dim context-id)
         (unless (eq status :ok)
           (return-from security-check (values status reason))))
       (values :ok "Expression passes all security checks")))))

;;; ============================================================
;;; Individual Checks
;;; ============================================================

(defun check-concept (concept-id context-id)
  "Check if concept is known and applicable.
   Returns (values status reason)."
  (let ((u (universe context-id)))
    (unless u
      (return-from check-concept (values :unknown-concept (format nil "Context ~a has no universe" context-id))))
    (unless (member concept-id u)
      (return-from check-concept (values :unknown-concept (format nil "Concept ~a not in universe of ~a" concept-id context-id)))))
  (values :ok nil))

(defun check-dimension (dim-id context-id)
  "Check if dimension exists and is applicable in context.
   Returns (values status reason)."
  (let ((ctx (gethash context-id *contexts*)))
    (unless ctx
      (return-from check-dimension (values :unknown-dimension (format nil "Context ~a not found" context-id))))
    (unless (member dim-id (getf ctx :dimensions))
      (return-from check-dimension (values :dimension-not-applicable
                                    (format nil "Dimension ~a not applicable in context ~a" dim-id context-id)))))
  (values :ok nil))

(defun check-value (dim-id value)
  "Check if value is valid for dimension.
   Returns (values status reason)."
  (let ((dim (gethash dim-id *dimensions*)))
    (unless dim
      (return-from check-value (values :unknown-dimension (format nil "Dimension ~a not found" dim-id))))
    (let ((valid-values (getf dim :values)))
      (unless (member value valid-values)
        (return-from check-value (values :unknown-value
                                      (format nil "Value ~a not valid for dimension ~a" value dim-id))))))
  (values :ok nil))

(defun check-type-compatibility (dim-id subject value)
  "Check if subject type matches dimension applicability.
   Returns (values status reason)."
  (declare (ignore value))
  (let ((dim (gethash dim-id *dimensions*)))
    (when dim
      (let ((applies-to (getf dim :applies-to)))
        (when applies-to
          (let ((subject-type (get-concept-type subject)))
            (unless (member subject-type applies-to)
              (return-from check-type-compatibility
                (values :type-mismatch
                        (format nil "Subject ~a (type ~a) not compatible with dimension ~a (requires ~a)"
                                subject subject-type dim-id applies-to)))))))))
  (values :ok nil))

(defun check-sense-mask (dim-id context-id)
  "Check if dimension is within sense mask for context.
   Returns (values status reason)."
  (let ((sense (sense-mask context-id)))
    (unless sense
      (return-from check-sense-mask (values :outside-sense-mask "No sense mask for context")))
    (let ((bit-dict (mask-signature-bit-dictionary sense))
          (dim-bit (assoc dim-id bit-dict :test #'equal)))
      (unless dim-bit
        (return-from check-sense-mask
          (values :outside-sense-mask
                  (format nil "Dimension ~a outside sense mask for context ~a" dim-id context-id))))))
  (values :ok nil))

;;; ============================================================
;;; Post-Processing Checks (after denote)
;;; ============================================================

(defun check-denotation (sig context-id)
  "Check denotation result for tautologies and contradictions.
   Returns (values status reason)."
  (let ((den (denote sig context-id))
        (u (universe context-id)))
    (cond
      ((null den)
       (values :no-denotation "Denotation is empty (⟦x⟧_K = ∅)"))
      ((= (length den) (length u))
       (values :tautological-query "Denotation equals universe (⟦x⟧_K = U)"))
      (t
       (values :ok nil)))))

;;; ============================================================
;;; Reference Resolution
;;; ============================================================

(defun resolve-reference (reference discourse-context)
  "Resolve ambiguous reference like 'this library', 'the previous one'.
   Returns concept-id or nil."
  (cond
    ((symbolp reference)
     (let ((resolved (cdr (assoc reference discourse-context :test #'equal))))
       (if resolved
           resolved
           (values nil :ambiguous-reference))))
    ((stringp reference)
     ;; Would call NL parser here
     (values nil :unknown-concept))
    (t
     (values reference :ok))))

;;; ============================================================
;;; Helper Functions
;;; ============================================================

(defun valid-concept-p (concept-id context-id)
  (multiple-value-bind (status reason) (check-concept concept-id context-id)
    (declare (ignore reason))
    (eq status :ok)))

(defun valid-dimension-p (dim-id context-id)
  (multiple-value-bind (status reason) (check-dimension dim-id context-id)
    (declare (ignore reason))
    (eq status :ok)))

(defun valid-value-p (dim-id value)
  (multiple-value-bind (status reason) (check-value dim-id value)
    (declare (ignore reason))
    (eq status :ok)))

(defun get-concept-type (concept-id)
  "Get type of concept. Placeholder."
  (declare (ignore concept-id))
  nil)

;;; ============================================================
;;; Classify Error for User-Friendly Messages
;;; ============================================================

(defun classify-error (error-keyword)
  "Return user-friendly message for error type."
  (case error-keyword
    (:unknown-concept         "No conozco el concepto mencionado")
    (:unknown-dimension       "No existe esa dimensión en el sistema")
    (:unknown-value           "Ese valor no es válido para la dimensión")
    (:type-mismatch          "El tipo de concepto no coincide con la dimensión")
    (:dimension-not-applicable "La dimensión no aplica en este contexto")
    (:outside-sense-mask      "La pregunta está fuera del sentido actual")
    (:malformed-signature     "La expresión está mal formada")
    (:no-denotation           "La consulta no denota ningún concepto")
    (:tautological-query      "La consulta es una tautología (todos los conceptos)")
    (:ambiguous-reference     "La referencia es ambigua")
    (t                        "Error desconocido")))

;;; ============================================================
;;; Example Usage (commented out)
;;; ============================================================

#|
;; Security check before processing
(let ((expr '(D_PARTE_COMESTIBLE C_LECHUGA hoja)))
  (multiple-value-bind (status reason) (security-check expr 'K_COCINA)
    (if (eq status :ok)
        (format t "Expression is safe to process~%")
        (format t "Blocked: ~a (~a)~%" (classify-error status) reason))))

;; Check concept
(check-concept 'C_LECHUGA 'K_COCINA)
;; => :ok, nil

;; Check unknown concept
(check-concept 'C_UNKNOWN 'K_COCINA)
;; => :unknown-concept, "Concept C_UNKNOWN not in universe..."

;; Resolve reference
(resolve-reference 'this_library '((this_library . PROJECT_X)))
;; => PROJECT_X
|#

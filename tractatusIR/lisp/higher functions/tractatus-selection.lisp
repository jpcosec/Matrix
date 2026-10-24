;;;; tractatus-selection.lisp
;;;; Dimension selection objective function for efficient search
;;;; Implements Turn 44 item 12: score(D) = info_gain - cost - uncertainty

(defpackage :tractatus-selection
  (:use :cl :tractatus-discrimination)
  (:export
   #:score-dimension
   #:information-gain
   #:cost
   #:uncertainty
   #:select-best-dimension
   #:entropy
   #:weighted-score))

(in-package :tractatus-selection)

;;; ============================================================
;;; Configuration
;;; ============================================================

(defparameter *w-info* 1.0
  "Weight for information gain")

(defparameter *w-cost* 0.5
  "Weight for observation cost")

(defparameter *w-uncertainty* 0.3
  "Weight for fact uncertainty")

;;; ============================================================
;;; Dimension Selection Objective Function
;;; score(D) = w₁·information_gain(D) - w₂·cost(D) - w₃·uncertainty(D)
;;; From Turn 44: "elegir dimensión que separa mejor"
;;; ============================================================

(defstruct dimension-score
  "Score breakdown for a dimension."
  (dimension nil :type symbol)
  (info-gain 0.0 :type float)
  (cost 0.0 :type float)
  (uncertainty 0.0 :type float)
  (total 0.0 :type float))

(defun score-dimension (dim-id m1 context-id &key (concepts nil))
  "Compute score for dimension D.
   score(D) = w₁·IG(D) - w₂·cost(D) - w₃·uncertainty(D)"
  (let* ((ig (information-gain dim-id m1 concepts))
         (c (cost dim-id context-id))
         (u (uncertainty dim-id context-id))
         (total (- (* *w-info* ig) (* *w-cost* c) (* *w-uncertainty* u))))
    (make-dimension-score
     :dimension dim-id
     :info-gain ig
     :cost c
     :uncertainty u
     :total (float total))))

(defun weighted-score (dim-id m1 context-id weights &key (concepts nil))
  "Compute weighted score with custom weights.
   weights: plist with :info, :cost, :uncertainty"
  (let* ((w-i (getf weights :info *w-info*))
         (w-c (getf weights :cost *w-cost*))
         (w-u (getf weights :uncertainty *w-uncertainty*))
         (ig (information-gain dim-id m1 concepts))
         (c (cost dim-id context-id))
         (u (uncertainty dim-id context-id))
         (total (- (* w-i ig) (* w-c c) (* w-u u))))
    (make-dimension-score
     :dimension dim-id
     :info-gain ig
     :cost c
     :uncertainty u
     :total (float total))))

;;; ============================================================
;;; Information Gain: Entropy Reduction
;;; IG(D) = H(U) - H(U|D)
;;; From Turn 44: "cuánto reduce colisiones"
;;; ============================================================

(defun information-gain (dim-id m1 concepts)
  "Compute information gain of dimension D.
   IG(D) = H(universe) - H(universe | D)"
  (declare (ignore dim-id))
  (let* ((u (or concepts (matrix-rows m1)))
         (h-u (entropy u))
         (h-conditioned (conditioned-entropy m1 concepts)))
    (max 0.0 (- h-u h-conditioned))))

(defun entropy (concepts)
  "Compute entropy of a set of concepts.
   H(S) = -Σ p_i · log₂(p_i)
   Uniform distribution if no frequency info."
  (let ((n (length concepts)))
    (if (<= n 1)
        0.0
        (let ((p (/ 1.0 n)))
          (* -1.0 n (* p (log p 2)))))))

(defun conditioned-entropy (m1 concepts)
  "Compute H(U|D) = Σ |bucket_v|/|U| · H(bucket_v)"
  (let* ((m1-t (m1-transpose m1))
         (buckets (buckets m1-t))
         (total (length concepts))
         (sum 0.0))
    (dolist (b buckets sum)
      (let* ((bucket-size (length (cdr b)))
             (p (/ (float bucket-size) total)))
        (when (> p 0.0)
          (incf sum (* p (entropy (cdr b)))))))))

;;; ============================================================
;;; Cost: Expense of Observing/Computing Dimension
;;; ============================================================

(defvar *dimension-costs* (make-hash-table :test 'eq)
  "Maps dimension-id to observation cost")

(defun cost (dim-id context-id)
  "Get cost of observing dimension D.
   Lower = cheaper to observe."
  (declare (ignore context-id))
  (or (gethash dim-id *dimension-costs*)
      1.0))  ; default cost

(defun set-cost (dim-id cost-value)
  "Set cost for a dimension."
  (setf (gethash dim-id *dimension-costs*) (float cost-value)))

;;; ============================================================
;;; Uncertainty: Reliability of Facts for Dimension
;;; From Turn 44: "qué tan confiables son los facts de esa dimensión"
;;; ============================================================

(defvar *dimension-uncertainty* (make-hash-table :test 'eq)
  "Maps dimension-id to uncertainty (0.0 = certain, 1.0 = very uncertain)")

(defun uncertainty (dim-id context-id)
  "Get uncertainty of facts for dimension D in context."
  (declare (ignore context-id))
  (or (gethash dim-id *dimension-uncertainty*)
      0.0))  ; default: no uncertainty

(defun set-uncertainty (dim-id uncertainty-value)
  "Set uncertainty for a dimension (0.0 to 1.0)."
  (setf (gethash dim-id *dimension-uncertainty*)
        (max 0.0 (min 1.0 (float uncertainty-value)))))

;;; ============================================================
;;; Select Best Dimension
;;; ============================================================

(defun select-best-dimension (dim-ids m1 context-id &key (concepts nil) (weights nil))
  "Select dimension with highest score.
   Returns (values best-dim best-score all-scores)."
  (let ((scores (loop for dim-id in dim-ids
                     collect (if weights
                               (weighted-score dim-id m1 context-id weights :concepts concepts)
                               (score-dimension dim-id m1 context-id :concepts concepts)))))
    (let ((best (car (sort scores #'> :key #'dimension-score-total))))
      (values (dimension-score-dimension best)
              best
              scores))))

;;; ============================================================
;;; Example Usage (commented out)
;;; ============================================================

#|
;; Setup dimensions and costs
(set-cost 'D_PARTE_COMESTIBLE 0.3)   ; easy to observe
(set-cost 'D_ESTRUCTURA_HOJA 0.7)   ; harder to observe
(set-uncertainty 'D_PARTE_COMESTIBLE 0.1)   ; reliable facts
(set-uncertainty 'D_ESTRUCTURA_HOJA 0.4)   ; less reliable

;; Score dimensions
(let* ((concepts '(C_LECHUGA C_ESPINACA C_ZANAHORIA C_APIO))
       (dim-ids '(D_PARTE_COMESTIBLE D_ESTRUCTURA_HOJA))
       (best-dim (select-best-dimension dim-ids *m1* 'K_COCINA :concepts concepts)))
  (format t "Best dimension: ~a~%" best-dim))

;; Information gain example
;; IG = entropy(universe) - entropy after splitting by D
;; High IG = good separator
|#

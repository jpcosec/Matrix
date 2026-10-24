;;;; tractatus-discrimination.lisp
;;;; Matrix representations, buckets, collisions, partition lattice
;;;; Implements M0, M1, M1ᵀ from specs/data_model/matrix_representation.md

(defpackage :tractatus-discrimination
  (:use :cl :tractatus-signatures)
  (:export
   #:make-m0
   #:make-m1
   #:m1-transpose
   #:bucket
   #:buckets
   #:collisions
   #:detect-collisions
   #:expand-submatrix
   #:horizontal-similarity
   #:partition-lattice
   #:search-tree))

(in-package :tractatus-discrimination)

;;; ============================================================
;;; Matrix Structures
;;; ============================================================

(defstruct matrix
  "A matrix with rows, columns, and data."
  (rows nil :type list)
  (cols nil :type list)
  (data nil :type list))

(defun make-matrix (rows cols data)
  "Create a matrix with given rows, columns, and 2D data."
  (make-matrix :rows rows :cols cols :data data))

(defun matrix-ref (m row col)
  "Get value at (row, col) in matrix."
  (let ((row-idx (position row (matrix-rows m) :test #'equal))
        (col-idx (position col (matrix-cols m) :test #'equal)))
    (unless (and row-idx col-idx)
      (return-from matrix-ref nil))
    (nth col-idx (nth row-idx (matrix-data m)))))

;;; ============================================================
;;; M0: Concept × Feature Matrix (base properties)
;;; From matrix_representation.md
;;; ============================================================

(defun make-m0 (concepts features concept-features)
  "Create M0: Concept × Feature matrix.
   concept-features: alist of (concept . (feature . value) ...)"
  (let ((data (loop for c in concepts
                   collect (loop for f in features
                             collect (or (cdr (assoc f (cdr (assoc c concept-features)) :test #'equal)) 0)))))
    (make-matrix concepts features data)))

;;; ============================================================
;;; M1: Concept × DiscriminantValue Matrix
;;; From matrix_representation.md
;;; ============================================================

(defun make-m1 (concepts dimension-values concept-values)
  "Create M1: Concept × DiscriminantValue matrix.
   concept-values: alist of (concept . (value . 1/0) ...)
   Uses one-hot encoding: exactly one value = 1 per concept."
  (let ((data (loop for c in concepts
                   collect (loop for v in dimension-values
                             collect (or (cdr (assoc v (cdr (assoc c concept-values)) :test #'equal)) 0)))))
    (make-matrix concepts dimension-values data)))

;;; ============================================================
;;; M1ᵀ: DiscriminantValue × Concept Matrix (Inverted Index)
;;; From matrix_representation.md: buckets / search buckets
;;; ============================================================

(defun m1-transpose (m1)
  "Compute M1ᵀ: DiscriminantValue × Concept.
   This is the inverted index / bucket representation."
  (let* ((concepts (matrix-rows m1))
         (values (matrix-cols m1))
         (data (matrix-data m1))
         (new-data (loop for v in values
                        for v-idx from 0
                        collect (loop for c in concepts
                                      for c-idx from 0
                                      collect (nth v-idx (nth c-idx data))))))
    (make-matrix values concepts new-data)))

;;; ============================================================
;;; Buckets: Direct Access to Concept Groups
;;; ============================================================

(defun buckets (m1-transpose)
  "Extract buckets from M1ᵀ.
   Returns alist: (value . (concept1 concept2 ...))"
  (let ((values (matrix-rows m1-transpose))
        (concepts (matrix-cols m1-transpose))
        (data (matrix-data m1-transpose)))
    (loop for v in values
          for v-idx from 0
          collect (cons v (loop for c in concepts
                               for c-idx from 0
                               when (= 1 (nth c-idx (nth v-idx data)))
                               collect c)))))

(defun bucket (m1-transpose value)
  "Get concepts in bucket for a specific value."
  (let ((bucket-alist (buckets m1-transpose)))
    (cdr (assoc value bucket-alist :test #'equal))))

;;; ============================================================
;;; Collision Detection
;;; From matrix_representation.md: |bucket(v)| > 1
;;; ============================================================

(defun collisions (m1-transpose)
  "Find values with more than one concept (collisions).
   Returns list of (value concept1 concept2 ...)."
  (let ((bucket-alist (buckets m1-transpose)))
    (remove-if #'(lambda (b) (<= (length (cdr b)) 1)) bucket-alist)))

(defun detect-collisions (m1-transpose)
  "Print collision report."
  (let ((colls (collisions m1-transpose)))
    (if (null colls)
        (format t "No collisions detected.~%")
        (dolist (c colls)
          (format t "Collision: value ~a has ~a concepts: ~a~%" (car c) (length (cdr c)) (cdr c))))
    colls))

;;; ============================================================
;;; Recursive Submatrix Expansion
;;; From matrix_representation.md: build submatrix for colliding subgroup
;;; ============================================================

(defstruct submatrix-tree
  "Tree structure for recursive submatrix expansion."
  (dimension nil :type symbol)
  (value nil :type t)
  (concepts nil :type list)
  (children nil :type list)  ; list of submatrix-tree
  (leaf-concept nil :type symbol))

(defun expand-submatrix (colliding-concepts dimension-hierarchy concept-dim-values)
  "Build submatrix tree for colliding concepts.
   dimension-hierarchy: list of (dimension . values) to expand.
   Returns submatrix-tree."
  (if (null dimension-hierarchy)
      ;; Leaf: single concept
      (make-submatrix-tree
       :concepts colliding-concepts
       :leaf-concept (car colliding-concepts))
      ;; Internal node: split by current dimension
      (let* ((dim (caar dimension-hierarchy))
             (values (cdar dimension-hierarchy))
             (rest-dims (cdr dimension-hierarchy))
             (children (loop for v in values
                            for subgroup = (remove-if-not
                                            #'(lambda (c)
                                                (equal (cdr (assoc dim (cdr (assoc c concept-dim-values)) :test #'equal)) v))
                                            colliding-concepts)
                            when subgroup
                            collect (expand-submatrix subgroup rest-dims concept-dim-values))))
        (make-submatrix-tree
         :dimension dim
         :concepts colliding-concepts
         :children children))))

;;; ============================================================
;;; Horizontal Similarity: M1 × M1ᵀ
;;; From matrix_representation.md: Concept × Concept similarity
;;; Boolean semiring: sum=OR, product=AND
;;; ============================================================

(defun horizontal-similarity (m1)
  "Compute M1 × M1ᵀ: Concept × Concept similarity matrix.
   S[i,j] = OR_k(M1[i,k] AND M1ᵀ[k,j])
   Interpretation: S[i,j] = 1 iff concepts i and j share a value in dimension."
  (let* ((concepts (matrix-rows m1))
         (values (matrix-cols m1))
         (data (matrix-data m1))
         (m1-t (m1-transpose m1))
         (new-data (loop for i from 0 below (length concepts)
                        collect (loop for j from 0 below (length concepts)
                                  collect (loop for k from 0 below (length values)
                                            when (and (= 1 (nth k (nth i data)))
                                                     (= 1 (nth j (nth k (matrix-data m1-t)))))
                                            return 1
                                            finally return 0)))))
    (make-matrix concepts concepts new-data)))

;;; ============================================================
;;; Partition Lattice
;;; From mathematical_formalization.md: Partitions(U) forms a lattice
;;; ============================================================

(defun partition-from-dimension (m1 dim-value)
  "Get partition induced by a dimension value.
   Returns list of buckets (concepts sharing same value)."
  (let ((m1-t (m1-transpose m1)))
    (buckets m1-t)))

(defun partition-lattice (m1-list)
  "Build lattice of partitions from multiple M1 matrices.
   Returns list of partitions sorted by refinement."
  (mapcar #'partition-from-dimension m1-list))

;;; ============================================================
;;; Search Tree from Collision Expansion
;;; From matrix_representation.md: search tree built from matrices
;;; ============================================================

(defun search-tree (concepts dimension-hierarchy concept-dim-values)
  "Build search tree from concepts using dimension hierarchy.
   dimension-hierarchy: list of (dimension . (value1 value2 ...)).
   Returns submatrix-tree."
  (expand-submatrix concepts dimension-hierarchy concept-dim-values))

;;; ============================================================
;;; Example Usage (commented out)
;;; ============================================================

#|
;; Define concepts and dimension values
(defparameter *concepts* '(C_LECHUGA C_ESPINACA C_ZANAHORIA C_APIO))
(defparameter *dim-values* '(hoja raiz tallo))

;; Concept values for D_PARTE_COMESTIBLE
(defparameter *concept-values*
  '((C_LECHUGA . ((hoja . 1) (raiz . 0) (tallo . 0)))
    (C_ESPINACA . ((hoja . 1) (raiz . 0) (tallo . 0)))
    (C_ZANAHORIA . ((hoja . 0) (raiz . 1) (tallo . 0)))
    (C_APIO . ((hoja . 0) (raiz . 0) (tallo . 1)))))

;; Create M1
(defparameter *m1* (make-m1 *concepts* *dim-values* *concept-values*))

;; Get M1ᵀ (buckets)
(defparameter *m1-t* (m1-transpose *m1*))

;; Get buckets
(buckets *m1-t*)
;; => ((hoja C_LECHUGA C_ESPINACA) (raiz C_ZANAHORIA) (tallo C_APIO))

;; Detect collisions
(detect-collisions *m1-t*)
;; => Collision: value hoja has 2 concepts: (C_LECHUGA C_ESPINACA)

;; Horizontal similarity
(defparameter *sim* (horizontal-similarity *m1*))
;; S[lechuga, espinaca] = 1 (share hoja)
;; S[lechuga, zanahoria] = 0
|#

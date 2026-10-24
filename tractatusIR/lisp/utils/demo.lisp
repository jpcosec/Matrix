;;;; demo.lisp
;;;; End-to-end demo of the Tractatus Lisp implementation
;;;; Exercises all major components

(defpackage :tractatus-demo
  (:use :cl :tractatus-signatures :tractatus-semantics
             :tractatus-discrimination :tractatus-update
             :tractatus-selection :tractatus-security
             :tractatus-parser :tractatus-inference
             :tractatus-versioning :tractatus-db :tractatus-nl2projection))

(in-package :tractatus-demo)

;;; ============================================================
;;; Setup: Initialize Everything
;;; ============================================================

(defun setup-demo ()
  "Initialize all components for demo."
  (format t "~%=== Setting up Tractatus Demo ===~%")
  
  ;; 1. Initialize DB
  (init-db :type :memory)
  (format t "✓ Database initialized~%")
  
  ;; 2. Define concepts
  (save-concept 'C_LECHUGA "lechuga" 
              :aliases '("lettuce" "Lactuca sativa"))
  (save-concept 'C_ESPINACA "espinaca")
  (save-concept 'C_ZANAHORIA "zanahoria")
  (save-concept 'C_APIO "apio")
  (format t "✓ Concepts saved~%")
  
  ;; 3. Define dimensions
  (save-dimension 'D_PARTE_COMESTIBLE "Parte comestible" :one-hot
                 :question "¿Qué parte se consume?")
  (save-dimension 'D_ESTRUCTURA "Estructura" :multi-hot)
  (format t "✓ Dimensions saved~%")
  
  ;; 4. Save dimension values
  (save-dimension-value 'V_HOJA 'D_PARTE_COMESTIBLE "hoja")
  (save-dimension-value 'V_RAIZ 'D_PARTE_COMESTIBLE "raíz")
  (save-dimension-value 'V_TALLO 'D_PARTE_COMESTIBLE "tallo")
  (format t "✓ Dimension values saved~%")
  
  ;; 5. Define context
  (defcontext 'K_COCINA_VERDURAS
    :dimensions '(D_PARTE_COMESTIBLE D_ESTRUCTURA)
    :universe '(C_LECHUGA C_ESPINACA C_ZANAHORIA C_APIO))
  (format t "✓ Context K_COCINA_VERDURAS created~%")
  
  ;; 6. Set up universe
  (setf (universe 'K_COCINA_VERDURAS) 
        '(C_LECHUGA C_ESPINACA C_ZANAHORIA C_APIO))
  
  ;; 7. Set up masks
  (setf (valid-mask 'K_COCINA_VERDURAS)
        (make-mask 'K_COCINA_VERDURAS :valid '(1 1 1)
                   '((0 . hoja_comestible) (1 . raiz_comestible) (2 . tallo_comestible))))
  (setf (sense-mask 'K_COCINA_VERDURAS)
        (make-mask 'K_COCINA_VERDURAS :sense '(1 1 1)
                   '((0 . hoja_comestible) (1 . raiz_comestible) (2 . tallo_comestible))))
  (setf (discriminative-mask 'K_COCINA_VERDURAS)
        (make-mask 'K_COCINA_VERDURAS :discriminative '(1 1 1)
                   '((0 . hoja_comestible) (1 . raiz_comestible) (2 . tallo_comestible))))
  (setf (observed-mask 'K_COCINA_VERDURAS)
        (make-mask 'K_COCINA_VERDURAS :observed '(1 1 1)
                   '((0 . hoja_comestible) (1 . raiz_comestible) (2 . tallo_comestible))))
  (format t "✓ Masks configured~%")
  
  ;; 8. Add facts
  (add-fact '(D_PARTE_COMESTIBLE C_LECHUGA hoja) :context-id 'K_COCINA_VERDURAS)
  (add-fact '(D_PARTE_COMESTIBLE C_ESPINACA hoja) :context-id 'K_COCINA_VERDURAS)
  (add-fact '(D_PARTE_COMESTIBLE C_ZANAHORIA raiz) :context-id 'K_COCINA_VERDURAS)
  (add-fact '(D_PARTE_COMESTIBLE C_APIO tallo) :context-id 'K_COCINA_VERDURAS)
  (format t "✓ Facts added~%")
  
  t)

;;; ============================================================
;;; Demo 1: Signature Creation and Validation
;;; ============================================================

(defun demo-signatures ()
  "Demo signature operations."
  (format t "~%~%=== Demo 1: Signatures ===~%")
  
  ;; Create concept signature
  (let* ((lechuga-sig (make-concept-sig 
                         'C_LECHUGA 
                         'K_COCINA_VERDURAS 
                         '(1 0 0)
                         '((0 . hoja) (1 . raiz) (2 . tallo)))))
    (format t "Lechuga signature: ~a~%" lechuga-sig)
    
    ;; Validate
    (let ((result (validate lechuga-sig 'K_COCINA_VERDURAS)))
      (format t "Validation status: ~a~%" (logical-result-status result))
      (format t "Denotation: ~a~%" (logical-result-denotation result)))
    
    ;; Check sense
    (let ((stat (status lechuga-sig 'K_COCINA_VERDURAS)))
      (format t "Sense status: ~a~%" stat))
    
    ;; Semantic AND
    (let* ((zanahoria-sig (make-concept-sig 
                            'C_ZANAHORIA 
                            'K_COCINA_VERDURAS 
                            '(0 1 0)
                            '((0 . hoja) (1 . raiz) (2 . tallo))))
           (and-result (semantic-and lechuga-sig zanahoria-sig 'K_COCINA_VERDURAS)))
      (format t "Lechuga AND Zanahoria: ~a~%" and-result))
    
    ;; Contrast
    (let ((contrast-result (contrast lechuga-sig zanahoria-sig 'K_COCINA_VERDURAS)))
      (format t "Contrast (Lechuga vs Zanahoria): ~a~%" contrast-result))))

;;; ============================================================
;;; Demo 2: Matrix and Discrimination
;;; ============================================================

(defun demo-discrimination ()
  "Demo matrix operations and collision detection."
  (format t "~%~%=== Demo 2: Discrimination ===~%")
  
  ;; Create M1 matrix
  (let* ((concepts '(C_LECHUGA C_ESPINACA C_ZANAHORIA C_APIO))
         (dim-values '(hoja raiz tallo))
         (concept-values
           '((C_LECHUGA . ((hoja . 1) (raiz . 0) (tallo . 0)))
             (C_ESPINACA . ((hoja . 1) (raiz . 0) (tallo . 0)))
             (C_ZANAHORIA . ((hoja . 0) (raiz . 1) (tallo . 0)))
             (C_APIO . ((hoja . 0) (raiz . 0) (tallo . 1)))))
         (m1 (make-m1 concepts dim-values concept-values)))
    
    (format t "M1 matrix created~%")
    
    ;; Get M1ᵀ (buckets)
    (let* ((m1-t (m1-transpose m1))
           (buckets (buckets m1-t)))
      (format t "Buckets: ~a~%" buckets))
    
    ;; Detect collisions
    (let ((colls (detect-collisions 'K_COCINA_VERDURAS)))
      (format t "Collisions: ~a~%" colls))
    
    ;; Horizontal similarity
    (let ((sim (horizontal-similarity m1)))
      (format t "Similarity matrix created~%"))))

;;; ============================================================
;;; Demo 3: Dimension Selection
;;; ============================================================

(defun demo-selection ()
  "Demo dimension selection."
  (format t "~%~%=== Demo 3: Dimension Selection ===~%")
  
  ;; Score dimensions
  (let* ((dim-ids '(D_PARTE_COMESTIBLE D_ESTRUCTURA))
         (concepts '(C_LECHUGA C_ESPINACA C_ZANAHORIA C_APIO)))
    
    (dolist (dim-id dim-ids)
      (let ((score (score-dimension dim-id nil 'K_COCINA_VERDURAS :concepts concepts)))
        (format t "Dimension ~a: info_gain=~a, cost=~a, uncertainty=~a, total=~a~%"
                dim-id
                (dimension-score-info-gain score)
                (dimension-score-cost score)
                (dimension-score-uncertainty score)
                (dimension-score-total score))))
    
    ;; Select best
    (multiple-value-bind (best-dim best-score all-scores)
        (select-best-dimension dim-ids nil 'K_COCINA_VERDURAS :concepts concepts)
      (format t "~%Best dimension: ~a (score: ~a)~%" best-dim (dimension-score-total best-score)))))

;;; ============================================================
;;; Demo 4: Security Checks
;;; ============================================================

(defun demo-security ()
  "Demo security taxonomy."
  (format t "~%~%=== Demo 4: Security ===~%")
  
  ;; Valid expression
  (multiple-value-bind (status reason) 
      (security-check '(D_PARTE_COMESTIBLE C_LECHUGA hoja) 'K_COCINA_VERDURAS)
    (format t "Valid expression: status=~a~%" status))
  
  ;; Unknown concept
  (multiple-value-bind (status reason) 
      (security-check '(D_PARTE_COMESTIBLE C_UNKNOWN hoja) 'K_COCINA_VERDURAS)
    (format t "Unknown concept: status=~a, reason=~a~%" status (classify-error status)))
  
  ;; Unknown dimension
  (multiple-value-bind (status reason) 
      (security-check '(D_UNKNOWN C_LECHUGA hoja) 'K_COCINA_VERDURAS)
    (format t "Unknown dimension: status=~a, reason=~a~%" status (classify-error status))))

;;; ============================================================
;;; Demo 5: Inference
;;; ============================================================

(defun demo-inference ()
  "Demo inference engine."
  (format t "~%~%=== Demo 5: Inference ===~%")
  
  ;; Define a rule
  (defrule 'R_SAME_BUCKET
    :type :logical
    :when '((D_PARTE_COMESTIBLE a hoja) (D_PARTE_COMESTIBLE b hoja))
    :then '((same_bucket a b D_PARTE_COMESTIBLE.hoja))
    :description "Same bucket inference")
  
  (format t "✓ Rule defined~%")
  
  ;; Run inference
  (let* ((facts '((D_PARTE_COMESTIBLE C_LECHUGA hoja)
                 (D_PARTE_COMESTIBLE C_ESPINACA hoja)))
         (inferred (logical-infer facts 'K_COCINA_VERDURAS)))
    (format t "Inferred facts: ~a~%" inferred)))

;;; ============================================================
;;; Demo 6: Context Versioning
;;; ============================================================

(defun demo-versioning ()
  "Demo context versioning."
  (format t "~%~%=== Demo 6: Versioning ===~%")
  
  ;; Check current version
  (format t "Current version: ~a~%" (get-current-version 'K_COCINA_VERDURAS))
  
  ;; Update to version 2
  (let ((ctx-v2 (update-context-version 'K_COCINA_VERDURAS
                :add-dimensions '(D_TEXTURA))))
    (format t "✓ Updated to version ~a~%" (context-version-version ctx-v2)))
  
  ;; List versions
  (let ((versions (context-versions 'K_COCINA_VERDURAS)))
    (format t "Versions: ~a~%" versions))
  
  ;; Rollback
  (rollback-context 'K_COCINA_VERDURAS 1)
  (format t "✓ Rolled back to version 1~%"))

;;; ============================================================
;;; Demo 7: NL2Projection
;;; ============================================================

(defun demo-nl2projection ()
  "Demo NL to Projection compilation."
  (format t "~%~%=== Demo 7: NL2Projection ===~%")
  
  ;; Parse natural language
  (let ((text "la lechuga tiene hoja comestible"))
    (format t "Input: ~s~%" text)
    (multiple-value-bind (sig ir) (parse text 'K_COCINA_VERDURAS)
      (if sig
          (format t "✓ Parsed! Signature: ~a, IR type: ~a~%" sig (projection-ir-type ir))
          (format t "✗ Parse failed~%"))))
  
  ;; Query
  (let ((text "busca vegetales de raíz"))
    (format t "~%Input: ~s~%" text)
    (multiple-value-bind (sig ir) (parse text 'K_COCINA_VERDURAS)
      (if sig
          (format t "✓ Parsed! Signature: ~a~%" sig)
          (format t "✗ Parse failed~%")))))

;;; ============================================================
;;; Run All Demos
;;; ============================================================

(defun run-all-demos ()
  "Run complete demo suite."
  (format t "~%")
  (format t "╔══════════════════════════════════════════════════════╗~%")
  (format t "║     TRACTATUS LISP IMPLEMENTATION DEMO              ║~%")
  (format t "╚══════════════════════════════════════════════════════╝~%")
  
  (setup-demo)
  (demo-signatures)
  (demo-discrimination)
  (demo-selection)
  (demo-security)
  (demo-inference)
  (demo-versioning)
  (demo-nl2projection)
  
  (format t "~%~%╔══════════════════════════════════════════════════════╗~%")
  (format t "║     DEMO COMPLETE                                    ║~%")
  (format t "╚══════════════════════════════════════════════════════╝~%"))

;;; ============================================================
;;; Entry Point
;;; ============================================================

(defun main ()
  "Main entry point."
  (run-all-demos))

;;; To run: (tractatus-demo:main)

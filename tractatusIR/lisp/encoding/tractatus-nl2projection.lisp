;;;; tractatus-nl2projection.lisp
;;;; Complete NL2Projection compiler pipeline
;;;; Implements specs/database/database_design.md pseudocode exactly

(defpackage :tractatus-nl2projection
  (:use :cl :tractatus-parser :tractatus-security :tractatus-semantics :tractatus-db)
  (:export
   #:nl2projection
   #:parse-nl
   #:detect-intent
   #:extract-entities
   #:resolve-context
   #:map-terms-to-dimensions
   #:map-terms-to-values
   #:build-ir-candidates
   #:compile-ir
   #:validate-ir
   #:execute-operation
   #:hybrid-parse))

(in-package :tractatus-nl2projection)

;;; ============================================================
;;; Main NL2Projection Pipeline (from spec pseudocode)
;;; parse_nl(text, candidate_contexts) -> List[ProjectionIR]
;;; ============================================================

(defun nl2projection (text &key (candidate-contexts nil) (use-llm nil))
  "Full NL2Projection compiler pipeline.
   Returns list of ProjectionIR candidates."
  (let* ((normalized (normalize text))
         (intent (detect-intent normalized))
         (entities (extract-entities normalized))
         (context-candidates (resolve-context normalized (or candidate-contexts (list-all-contexts))))
         (dimension-candidates (map-terms-to-dimensions normalized))
         (value-candidates (map-terms-to-values normalized))
         (ir-candidates (build-ir-candidates
                         :intent intent
                         :entities entities
                         :context-candidates context-candidates
                         :dimension-candidates dimension-candidates
                         :value-candidates value-candidates)))
    ;; If use-llm, enhance with LLM candidates
    (if use-llm
        (append ir-candidates (llm-enhance-candidates text ir-candidates))
        ir-candidates)))

(defun parse-nl (text &key (candidate-contexts nil) (use-llm nil))
  "Alias for nl2projection for backward compatibility."
  (nl2projection text :candidate-contexts candidate-contexts :use-llm use-llm))

;;; ============================================================
;;; Step 1: Normalize
;;; ============================================================

(defun normalize (text)
  "Normalize text: lowercase, remove accents, standardize punctuation."
  (let ((norm (string-downcase text)))
    ;; Remove extra whitespace
    (setf norm (regex-replace-all "\\s+" norm " "))
    ;; Could add accent removal here
    (string-trim " " norm)))

(defun regex-replace-all (pattern string replacement)
  "Simple regex replace. Placeholder for CL-PPCRE."
  (declare (ignore pattern replacement))
  string)

;;; ============================================================
;;; Step 2: Detect Intent
;;; From spec: lookup | contrast | insert | explain | define_dimension
;;; ============================================================

(defparameter *intent-patterns*
  '((:concept-assertion . ("es" "es una" "tiene" "clasific"))
    (:query . ("busca" "encuentra" "qué" "cuál" "dónde" "cómo"))
    (:contrast . ("diferencia" "contraste" "versus" "vs" "compar"))
    (:similarity-request . ("similar" "parecido" "como" "relacionado"))
    (:insert-concept . ("agrega" "añade" "nuevo" "crear"))
    (:define-dimension . ("separar" "diferenciar por" "agrupar por" "clasificar por"))
    (:refine-collision . ("refinar" "colisión" "colision" "resolver"))
    (:explain . ("por qué" "explícame" "razón" "cómo es" "qué es")))
  "Pattern matching for intent detection")

(defun detect-intent (normalized-text)
  "Detect intent from normalized text.
   Returns intent keyword."
  (let ((best-match nil)
        (best-score 0))
    (dolist (pair *intent-patterns*)
      (let ((intent (car pair))
            (patterns (cdr pair)))
        (dolist (pattern patterns)
          (when (search pattern normalized-text)
            (let ((score (length pattern)))
              (when (> score best-score)
                (setf best-match intent)
                (setf best-score score)))))))
    (or best-match :query)))  ; default to query

;;; ============================================================
;;; Step 3: Extract Entities
;;; Map words to concepts/dimensions/values
;;; ============================================================

(defun extract-entities (normalized-text)
  "Extract entities from text.
   Returns plist: (:concepts ...) (:dimensions ...) (:values ...)"
  (let ((tokens (split-sequence:split-sequence #\Space normalized-text :remove-empty-subseqs t))
        (entities (list :concepts nil :dimensions nil :values nil)))
    (dolist (token tokens)
      ;; Try concept
      (let ((concept (resolve-concept token)))
        (when concept
          (push concept (getf entities :concepts))))
      ;; Try dimension
      (let ((dim (resolve-dimension-from-term token)))
        (when dim
          (push dim (getf entities :dimensions))))
      ;; Try value
      (let ((value (resolve-value-from-term token)))
        (when value
          (push value (getf entities :values)))))
    entities))

(defun resolve-concept (token)
  "Resolve token to concept symbol."
  (let ((candidate (intern (string-upcase token))))
    (when (valid-concept-p candidate nil)  ; would need context
      candidate)))

(defun resolve-dimension-from-term (token)
  "Resolve token to dimension symbol."
  (let ((candidate (intern (string-upcase token))))
    (when (gethash candidate *dimensions*)
      candidate)))

(defun resolve-value-from-term (token)
  "Resolve token to value."
  (declare (ignore token))
  nil)  ; placeholder

;;; ============================================================
;;; Step 4: Resolve Context
;;; ============================================================

(defun resolve-context (normalized-text candidate-contexts)
  "Resolve context from text and candidates.
   Returns list of (context-id . confidence)."
  (let ((results nil))
    (dolist (ctx candidate-contexts)
      (let ((confidence (compute-context-confidence normalized-text ctx)))
        (push (cons ctx confidence) results)))
    (sort results #'> :key #'cdr)))

(defun compute-context-confidence (text context-id)
  "Compute confidence that context matches text."
  (declare (ignore text))
  (let ((ctx (load-context context-id)))
    (if ctx
        0.5  ; placeholder: would analyze domain/task match
        0.0)))

(defun list-all-contexts ()
  "List all context IDs."
  (let ((contexts nil))
    (maphash #'(lambda (k v) (declare (ignore v)) (push k contexts)) *contexts-table*)
    contexts))

;;; ============================================================
;;; Step 5 & 6: Map Terms to Dimensions/Values
;;; ============================================================

(defun map-terms-to-dimensions (normalized-text)
  "Map text terms to possible dimensions.
   Returns list of (dimension-id . confidence)."
  (let ((tokens (split-sequence:split-sequence #\Space normalized-text :remove-empty-subseqs t))
        (results nil))
    (dolist (token tokens)
      (maphash #'(lambda (dim-id dim-data)
                   (when (or (search token (getf dim-data :label) :test #'char-equal)
                             (search token (symbol-name dim-id) :test #'char-equal))
                     (push (cons dim-id 0.8) results)))
               *dimensions-table*))
    results))

(defun map-terms-to-values (normalized-text)
  "Map text terms to possible values.
   Returns list of (dimension-id value-id . confidence)."
  (let ((tokens (split-sequence:split-sequence #\Space normalized-text :remove-empty-subseqs t))
        (results nil))
    (dolist (token tokens)
      (maphash #'(lambda (key data)
                   (declare (ignore key))
                   (when (search token (getf data :value) :test #'char-equal)
                     (push (cons (getf data :dimension-id) (getf data :value-id)) results)))
               *dimension-values-table*))
    results))

;;; ============================================================
;;; Step 7: Build IR Candidates
;;; From spec: build_ir_candidates()
;;; ============================================================

(defun build-ir-candidates (&key intent entities context-candidates dimension-candidates value-candidates)
  "Build ProjectionIR candidates from parsed components.
   Returns list of ProjectionIR."
  (let ((candidates nil))
    ;; Create IR for each context candidate
    (dolist (ctx-entry context-candidates)
      (let* ((context-id (car ctx-entry))
             (ir (make-projection-ir
                   :type (intent-to-type intent)
                   :context-id context-id
                   :original-text "")))
        ;; Add constraints from dimension/value candidates
        (setf (projection-ir-constraints ir)
              (build-constraints dimension-candidates value-candidates context-id))
        (push ir candidates)))
    candidates))

(defun intent-to-type (intent)
  "Convert intent keyword to ProjectionIR type."
  (case intent
    (:concept-assertion :dimension)
    (:query :dimension)
    (:contrast :contrast)
    (:similarity-request :query)
    (:insert-concept :dimension)
    (:define-dimension :define-dimension)
    (:refine-collision :refine-collision)
    (:explain :explain)
    (t :dimension)))

(defun build-constraints (dimension-candidates value-candidates context-id)
  "Build constraints list from candidates.
   Returns list of (dimension value)."
  (let ((constraints nil))
    (dolist (dc dimension-candidates)
      (let ((dim-id (car dc)))
        ;; Find matching value
        (let ((value (find-value-for-dimension dim-id value-candidates)))
          (when value
            (push (list :dimension dim-id :operator := :value value) constraints)))))
    constraints))

(defun find-value-for-dimension (dim-id value-candidates)
  "Find value for dimension from candidates."
  (cdr (assoc dim-id value-candidates :test #'equal)))

;;; ============================================================
;;; Step 8: Compile IR to Signature
;;; From spec: compile_ir(ir, db) -> Signature
;;; ============================================================

(defun compile-ir (ir db)
  "Compile ProjectionIR to typed signature.
   Returns signature object."
  (declare (ignore db))
  (let* ((context-id (projection-ir-context-id ir))
         (constraints (projection-ir-constraints ir))
         (bit-count (get-context-bit-count context-id))
         (bits (make-array bit-count :initial-element 0))
         (valid (make-array bit-count :initial-element 0)))
    ;; Process constraints
    (dolist (constraint constraints)
      (let* ((dim (getf constraint :dimension))
             (value (getf constraint :value))
             (bit-index (resolve-bit context-id dim value)))
        (when bit-index
          (setf (aref bits bit-index) 1)
          (setf (aref valid bit-index) 1))))
    ;; Create appropriate signature type
    (case (projection-ir-type ir)
      (:dimension
       (make-concept-sig (extract-subject-from-ir ir) context-id
                          (coerce bits 'list) nil))
      (:query
       (make-query-sig context-id (coerce bits 'list) nil))
      (:contrast
       (make-contrast-sig nil nil context-id (coerce bits 'list) nil))
      (t nil))))

(defun get-context-bit-count (context-id)
  "Get bit count for context."
  (declare (ignore context-id))
  3)  ; placeholder

(defun resolve-bit (context-id dim-id value)
  "Resolve dimension+value to bit index."
  (declare (ignore context-id))
  (let ((key (cons dim-id value)))
    (gethash key *dimension-values-table*)))

(defun extract-subject-from-ir (ir)
  "Extract subject concept from IR."
  (let ((entities (projection-ir-entities ir)))
    (car (getf entities :concepts))))

;;; ============================================================
;;; Step 9: Validate IR with Grammar Γ
;;; From spec: validate_ir(ir, db) -> LogicalResult
;;; ============================================================

(defun validate-ir (ir db)
  "Validate IR with sense rules (Γ).
   Returns LogicalResult."
  (declare (ignore db))
  (let* ((signature (compile-ir ir nil))
         (context-id (projection-ir-context-id ir)))
    (unless signature
      (return-from validate-ir
        (make-logical-result
         :signature nil
         :status :unsinnig
         :reason "Failed to compile IR to signature")))
    ;; Security check
    (multiple-value-bind (sec-status sec-reason) (security-check-helper ir)
      (unless (eq sec-status :ok)
        (return-from validate-ir
          (make-logical-result
           :signature signature
           :status :unsinnig
           :reason sec-reason))))
    ;; Validate with Γ
    (let ((validation-result (validate signature context-id)))
      (case (logical-result-status validation-result)
        (:unsinnig
         (make-logical-result
          :signature signature
          :status :unsinnig
          :reason "Violates grammar Γ"))
        (:outside-context
         (make-logical-result
          :signature signature
          :status :outside-context
          :reason "Dimension not in sense_mask for this context"))
        (t
         ;; Check denotation
         (let ((den (denote signature context-id)))
           (cond
             ((null den)
              (make-logical-result
               :signature signature
               :status :sinnlos-contradiction
               :denotation nil))
             ((= (length den) (length (universe context-id)))
              (make-logical-result
               :signature signature
               :status :sinnlos-tautology
               :denotation den))
             (t
              (make-logical-result
               :signature signature
               :status :sinnvoll
               :denotation den)))))))))

(defun security-check-helper (ir)
  "Run security check on IR."
  (let ((context-id (projection-ir-context-id ir)))
    (security-check nil context-id)))  ; placeholder

;;; ============================================================
;;; Step 10: Execute Operation
;;; ============================================================

(defun execute-operation (ir signature validation-result)
  "Execute operation based on IR type and validation."
  (let ((status (logical-result-status validation-result)))
    (unless (eq status :sinnvoll)
      (return-from execute-operation
        (values nil status (logical-result-reason validation-result))))
    (case (projection-ir-type ir)
      (:query
       (denote signature (projection-ir-context-id ir)))
      (:concept-assertion
       (add-fact-from-ir ir))
      (:insert-concept
       (insert-concept-from-ir ir))
      (:explain
       (verbalize signature (projection-ir-context-id ir)))
      (t
       (values signature :ok nil)))))

(defun add-fact-from-ir (ir)
  "Add fact from IR."
  (declare (ignore ir))
  ;; Would call add-fact
  t)

(defun insert-concept-from-ir (ir)
  "Insert concept from IR."
  (declare (ignore ir))
  ;; Would call add-concept
  t)

;;; ============================================================
;;; Hybrid LLM + Deterministic Resolver
;;; From spec: LLM proposes → deterministic resolver validates
;;; ============================================================

(defun hybrid-parse (text &key (candidate-contexts nil))
  "Hybrid parse: LLM candidates + deterministic resolution."
  (let* ((llm-candidates (llm-parse text))  ; would call LLM API
         (deterministic-candidates (nl2projection text :candidate-contexts candidate-contexts))
         (merged (merge-and-resolve llm-candidates deterministic-candidates)))
    (validate-and-select merged)))

(defun llm-parse (text)
  "Get LLM candidates.
   Placeholder: would call OpenAI/Claude API."
  (declare (ignore text))
  nil)

(defun merge-and-resolve (llm-candidates deterministic-candidates)
  "Merge LLM and deterministic candidates, resolve conflicts."
  (append deterministic-candidates llm-candidates))

(defun validate-and-select (candidates)
  "Validate candidates and select best."
  (let ((results nil))
    (dolist (c candidates)
      (let ((validation (validate-ir c nil)))
        (when (eq (logical-result-status validation) :sinnvoll)
          (push (cons c validation) results))))
    (car results)))  ; return best candidate

;;; ============================================================
;;; Dimension Learning: Propose New Dimension
;;; From spec: when parser can't find dimension, propose new one
;;; ============================================================

(defun propose-dimension (text context-id)
  "Propose a new dimension when parser can't find one.
   Returns DimensionProposal."
  (let* ((tokens (split-sequence:split-sequence #\Space text :remove-empty-subseqs t))
         (candidate-label (guess-dimension-label tokens))
         (candidate-values (guess-dimension-values tokens)))
    (list :status :pending-review
          :label candidate-label
          :type :one-hot  ; would guess better
          :values candidate-values
          :applies-when (guess-applies-when context-id)
          :source-text text)))

(defun guess-dimension-label (tokens)
  "Guess dimension label from tokens."
  (format nil "D_~a" (car (last tokens))))

(defun guess-dimension-values (tokens)
  "Guess possible values from tokens."
  (declare (ignore tokens))
  nil)

(defun guess-applies-when (context-id)
  "Guess applies_when from context."
  (let ((ctx (load-context context-id)))
    (when ctx
      (getf ctx :domain))))

;;; ============================================================
;;; Example Usage (commented out)
;;; ============================================================

#|
;; Full pipeline
(let* ((text "busca vegetales cuya parte comestible sea raíz")
       (candidates (nl2projection text :candidate-contexts '(K_COCINA_VERDURAS))))
  (dolist (ir candidates)
    (let* ((sig (compile-ir ir nil))
           (validation (validate-ir ir nil)))
      (format t "IR: ~a~%Signature: ~a~%Status: ~a~%"
              (projection-ir-type ir) sig (logical-result-status validation)))))

;; Hybrid parse
(hybrid-parse "la zanahoria está viva" :candidate-contexts '(K_COCINA_VERDURAS))

;; Propose dimension
(propose-dimension "distínguelas por si son crujientes o blandas" 'K_COCINA_VERDURAS)
|#

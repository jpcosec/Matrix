;;;; tractatus-parser.lisp
;;;; Parser: NL → ProjectionIR → Signature
;;;; Implements Turn 44 item 11: compilation from natural language

(defpackage :tractatus-parser
  (:use :cl :tractatus-signatures :tractatus-security)
  (:export
   #:parse
   #:compile-to-projection
   #:decompile-to-nl
   #:verbalize
   #:parse-dimension-query
   #:parse-relation-query
   #:make-projection-ir))

(in-package :tractatus-parser)

;;; ============================================================
;;; Projection Intermediate Representation
;;; ============================================================

(defstruct projection-ir
  "Intermediate representation between NL and signature.
   Maps to ProjectionIR from Turn 38."
  (type nil :type keyword)  ; :dimension, :relation, :query
  (dimension nil :type symbol)
  (subject nil :type symbol)
  (value nil :type t)
  (predicate nil :type symbol)
  (args nil :type list)
  (context-id nil :type symbol)
  (original-text nil :type string))

;;; ============================================================
;;; Main Parse Function
;;; NL → ProjectionIR → Signature
;;; ============================================================

(defun parse (text context-id &key (discourse-context nil))
  "Parse natural language text into a signature.
   Returns (values signature projection-ir) or (values nil error-status)."
  (let ((tokens (tokenize text)))
    ;; Resolve discourse references
    (when discourse-context
      (setf tokens (resolve-tokens tokens discourse-context)))
    ;; Try dimension query: "D(c)=v"
    (let ((ir (try-parse-dimension-query tokens context-id)))
      (when ir
        (return-from parse (compile-to-signature ir))))
    ;; Try relation query: "R(a,b)"
    (let ((ir (try-parse-relation-query tokens context-id)))
      (when ir
        (return-from parse (compile-to-signature ir))))
    ;; Try natural language patterns
    (let ((ir (try-parse-nl-patterns text context-id)))
      (when ir
        (return-from parse (compile-to-signature ir))))
    ;; Security check failed or unrecognized
    (values nil :parse-failed)))

(defun tokenize (text)
  "Simple tokenizer: split on whitespace and punctuation."
  (let ((clean (string-downcase text)))
    (loop for start = 0 then (1+ end)
          for end = (position-if #'(lambda (c) (member c '(#\Space #\, #\. #\; #\: #\! #\?))) clean :start start)
          for token = (subseq clean start end)
          when (> (length token) 0)
          collect token
          until (null end))))

;;; ============================================================
;;; Dimension Query Parsing: "D(c)=v" or "what is the X of Y?"
;;; ============================================================

(defun try-parse-dimension-query (tokens context-id)
  "Parse dimension query patterns."
  ;; Pattern: "D(c)=v" or "c tiene v"
  (when (>= (length tokens) 3)
    (let ((subject (intern (string-upcase (first tokens))))
          (dim-token (second tokens))
          (value-token (third tokens)))
      (let ((dim (resolve-dimension dim-token context-id))
            (value (resolve-value value-token dim)))
        (when (and dim value)
          (return-from try-parse-dimension-query
            (make-projection-ir
             :type :dimension
             :dimension dim
             :subject subject
             :value value
             :context-id context-id))))))
  ;; Pattern: "what is the X of Y?"
  (when (and (>= (length tokens) 5)
             (member "what" tokens :test #'string=)
             (member "of" tokens :test #'string=))
    (let* ((of-pos (position "of" tokens :test #'string=))
           (subject-token (nth (1+ of-pos) tokens))
           (dim-token (nth (1- of-pos) tokens))
           (subject (intern (string-upcase subject-token)))
           (dim (resolve-dimension dim-token context-id)))
      (when dim
        (return-from try-parse-dimension-query
          (make-projection-ir
           :type :dimension
           :dimension dim
           :subject subject
           :value nil  ; unknown, will query
           :context-id context-id)))))
  nil)

;;; ============================================================
;;; Relation Query Parsing: "R(a,b)"
;;; ============================================================

(defun try-parse-relation-query (tokens context-id)
  "Parse relation query patterns."
  ;; Pattern: "a imports b" or "a uses b"
  (when (>= (length tokens) 3)
    (let ((subj-token (first tokens))
          (pred-token (second tokens))
          (obj-token (third tokens)))
      (let ((pred (resolve-predicate pred-token context-id))
            (subj (intern (string-upcase subj-token)))
            (obj (intern (string-upcase obj-token))))
        (when pred
          (return-from try-parse-relation-query
            (make-projection-ir
             :type :relation
             :predicate pred
             :args (list subj obj)
             :context-id context-id))))))
  nil)

;;; ============================================================
;;; NL Pattern Parsing
;;; ============================================================

(defun try-parse-nl-patterns (text context-id)
  "Parse common NL patterns."
  (let ((lower (string-downcase text)))
    ;; Pattern: "la X es una Y" → D_TYPE(X)=Y
    (let ((match (search " es una " lower)))
      (when match
        (let* ((subj-token (subseq lower 0 match))
               (type-token (subseq lower (+ match 9)))
               (subject (intern (string-upcase subj-token)))
               (dim 'D_TYPE)
               (value (intern (string-upcase type-token))))
          (return-from try-parse-nl-patterns
            (make-projection-ir
             :type :dimension
             :dimension dim
             :subject subject
             :value value
             :context-id context-id)))))
    ;; Pattern: "X tiene Y Z" → D_Y(X)=Z
    (let ((words (tokenize lower)))
      (when (and (>= (length words) 4) (string= (second words) "tiene"))
        (let* ((subject (intern (string-upcase (first words))))
               (dim-token (third words))
               (value-token (fourth words))
               (dim (resolve-dimension dim-token context-id))
               (value (resolve-value value-token dim)))
          (when (and dim value)
            (return-from try-parse-nl-patterns
              (make-projection-ir
               :type :dimension
               :dimension dim
               :subject subject
               :value value
               :context-id context-id)))))))
  nil)

;;; ============================================================
;;; Compile ProjectionIR → Signature
;;; ============================================================

(defun compile-to-signature (ir)
  "Compile ProjectionIR to a typed signature.
   Returns (values signature projection-ir)."
  (case (projection-ir-type ir)
    (:dimension
     (let ((sig (compile-dimension-to-sig ir)))
       (values sig ir)))
    (:relation
     (let ((sig (compile-relation-to-sig ir)))
       (values sig ir)))
    (t
     (values nil ir))))

(defun compile-dimension-to-sig (ir)
  "Convert dimension IR to ConceptSignature or QuerySignature."
  (let ((dim (projection-ir-dimension ir))
        (subject (projection-ir-subject ir))
        (value (projection-ir-value ir))
        (ctx (projection-ir-context-id ir)))
    (if value
        ;; Complete: D(c)=v → ConceptSignature
        (let ((bits (encode-dimension-value dim value ctx)))
          (make-concept-sig subject ctx bits (list (cons dim value))))
        ;; Incomplete: D(c)=? → QuerySignature
        (make-query-sig ctx nil (list (cons dim :unknown))))))

(defun compile-relation-to-sig (ir)
  "Convert relation IR to QuerySignature."
  (declare (ignore ir))
  ;; Placeholder: would encode relation as query
  nil)

(defun encode-dimension-value (dim value context-id)
  "Encode dimension=value as bit vector."
  (let ((dim-data (gethash dim *dimensions*)))
    (when dim-data
      (let ((values (getf dim-data :values)))
        (loop for v in values
              collect (if (equal v value) 1 0))))))

;;; ============================================================
;;; Decompile: Signature → NL
;;; Turn 44 item 11: Signature → explanation
;;; ============================================================

(defun decompile-to-nl (sig &key (style :default))
  "Convert signature back to natural language.
   style: :default, :technical, :user-friendly"
  (declare (ignore style))
  (let ((bits (slot-value sig 'bits))
        (bit-dict (slot-value sig 'bit-dictionary)))
    (format nil "Signature: ~a~%Bits: ~a" bit-dict bits)))

(defun verbalize (sig context-id &key (style :default))
  "Generate human-readable explanation.
   Implements verbalize(signature, context, style) → text"
  (let ((den (denote sig context-id)))
    (format nil "En contexto ~a, la firma denota ~a concetos: ~a"
            context-id (length den) den)))

;;; ============================================================
;;; Helper Functions
;;; ============================================================

(defun resolve-dimension (token context-id)
  "Resolve token to dimension symbol."
  (let ((dim-id (intern (string-upcase token))))
    (if (valid-dimension-p dim-id context-id)
        dim-id
        nil)))

(defun resolve-value (token dim-id)
  "Resolve token to valid value for dimension."
  (let ((value (intern (string-upcase token))))
    (if (valid-value-p dim-id value)
        value
        nil)))

(defun resolve-predicate (token context-id)
  "Resolve token to predicate symbol."
  (declare (ignore context-id))
  (intern (string-upcase token)))

(defun resolve-tokens (tokens discourse-context)
  "Resolve discourse references in tokens."
  (loop for token in tokens
        collect (let ((resolved (cdr (assoc (intern (string-upcase token)) discourse-context :test #'equal))))
                  (if resolved
                      (string-downcase (symbol-name resolved))
                      token))))

(defun make-projection-ir (&key type dimension subject value predicate args context-id original-text)
  (make-instance 'projection-ir
                 :type type
                 :dimension dimension
                 :subject subject
                 :value value
                 :predicate predicate
                 :args args
                 :context-id context-id
                 :original-text original-text))

;;; ============================================================
;;; Example Usage (commented out)
;;; ============================================================

#|
;; Parse NL query
(multiple-value-bind (sig ir) (parse "la lechuga tiene hoja comestible" 'K_COCINA)
  (when sig
    (format t "Parsed: ~a~%" ir)
    (format t "Signature: ~a~%" sig)))

;; Compile to projection
(let ((ir (make-projection-ir
            :type :dimension
            :dimension 'D_PARTE_COMESTIBLE
            :subject 'C_LECHUGA
            :value 'hoja
            :context-id 'K_COCINA)))
  (compile-to-signature ir))

;; Verbalize
(verbalize *lechuga-sig* 'K_COCINA)
;; => "En contexto K_COCINA, la firma denota 1 conceptos: (C_LECHUGA)"
|#

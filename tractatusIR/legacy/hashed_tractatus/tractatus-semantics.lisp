;;;; tractatus-semantics.lisp
;;;; Semantic datatypes, signatures, and formal propositional model.

(defpackage #:tractatus-semantics
  (:use #:cl)
  (:export #:signature
           #:make-signature
           #:signature-bits
           #:signature-valid-mask
           #:signature-observed-mask
           #:signature-context-id
           #:signature-type
           #:signature-status
           #:fact
           #:fact-subject
           #:fact-predicate
           #:fact-object
           #:fact-context
           #:relation
           #:relation-predicate
           #:relation-args
           #:relation-context
           #:logical-status
           #:semantic-and
           #:semantic-or
           #:semantic-xor
           #:validate-signature
           #:project-to-signature))

(in-package #:tractatus-semantics)

;;; ==========================================
;;; 1. TIPOS DE ESTADO LOGICO
;;; ==========================================

(defparameter *logical-statuses*
  '(:sinnvoll              ; Con sentido: selecciona un subconjunto propio no vacio.
    :sinnlos-tautology     ; Tautologia: selecciona todo el universo local.
    :sinnlos-contradiction ; Contradiccion: selecciona el conjunto vacio.
    :unsinnig              ; Sinsentido: mal formado o no proyectable.
    :outside-context       ; Fuera de contexto: valido pero fuera de la mascara de sentido.
    :unknown               ; Desconocido: falta de informacion observada.
    :not-applicable))      ; No aplicable: la dimension no aplica al concepto.

;;; ==========================================
;;; 2. ESTRUCTURAS DE DATOS SEMANTICAS
;;; ==========================================

(defstruct signature
  (bits nil :type (or null string bit-vector))
  (valid-mask nil :type (or null string bit-vector))
  (observed-mask nil :type (or null string bit-vector))
  (context-id nil)
  (type :concept) ; :concept, :query, :contrast, :mask
  (status :unknown))

(defclass fact (tractatus-core::node)
  ((subject :initarg :subject :reader fact-subject)
   (predicate :initarg :predicate :reader fact-predicate)
   (object :initarg :object :reader fact-object)
   (context :initarg :context :reader fact-context)
   (truth-status :initarg :truth-status :initform :asserted-true :reader truth-status)
   (confidence :initarg :confidence :initform 1.0 :reader confidence)
   (source :initarg :source :initform nil :reader source)))

(defclass relation (tractatus-core::node)
  ((predicate :initarg :predicate :reader relation-predicate)
   (args :initarg :args :reader relation-args)
   (context :initarg :context :reader relation-context)
   (truth-status :initarg :truth-status :initform :asserted-true :reader truth-status)))

;;; ==========================================
;;; 3. OPERACIONES SEMANTICAS PARCIALES
;;; ==========================================

(defun validate-signature (sig context)
  "Verifica si una firma es semánticamente admisible según la gramática de sentido (Γ)."
  ;; Placeholder para la validacion real
  (declare (ignore context))
  (setf (signature-status sig) :sinnvoll)
  sig)

(defun semantic-xor (sig-a sig-b context)
  "Opera XOR entre dos firmas, produciendo una ContrastSignature validada."
  (declare (ignore context))
  (let ((bits-a (signature-bits sig-a))
        (bits-b (signature-bits sig-b)))
    ;; Placeholder: asumiendo strings de bits por ahora
    (make-signature :bits (format nil "XOR(~A,~A)" bits-a bits-b)
                    :type :contrast
                    :status :sinnvoll)))

(defun semantic-and (sig-a sig-b context)
  "Opera AND semántico (intersección de restricciones)."
  (declare (ignore sig-a sig-b context))
  (error "semantic-and no implementado todavía."))

(defun semantic-or (sig-a sig-b context)
  "Opera OR semántico (unión de posibilidades)."
  (declare (ignore sig-a sig-b context))
  (error "semantic-or no implementado todavía."))

(defun project-to-signature (concept context)
  "Proyecta un concepto en un contexto local generando su ConceptSignature."
  (declare (ignore concept context))
  (error "project-to-signature no implementado todavía."))

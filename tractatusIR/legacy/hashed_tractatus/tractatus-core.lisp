;;;; tractatus-core.lisp
;;;; El Microkernel de la Verdad (Truth Machine)

(defpackage #:tractatus-core
  (:use #:cl))
(in-package #:tractatus-core)

;;; ==========================================
;;; 1. BOOTSTRAP ONTOLOGICO (Los Meta-Tipos)
;;; ==========================================
;; Todo en el sistema hereda de un Nodo base indexable por su Hash (Content-Addressable)

(defclass node ()
  ((hash-id :initarg :hash-id :reader hash-id)))

(defclass begriff (node)
  ((subclase-de :initarg :subclase-de :initform nil :reader subclase-de)))

(defclass gegenstand (node)
  ((instancia-de :initarg :instancia-de :reader instancia-de)))

(defclass sachverhalt (node)
  ((objekte :initarg :objekte :reader objekte)
   (struktur :initarg :struktur :reader struktur)))

(defclass tatsache (node)
  ((von :initarg :von :reader von)))

(defclass welt (node)
  ((tatsachen :initform (make-hash-table :test 'equal) :accessor welt-tatsachen)
   (taxonomia :initform (make-hash-table :test 'equal) :accessor welt-taxonomia)
   (nombres   :initform (make-hash-table :test 'equal) :accessor welt-nombres)))

;;; ==========================================
;;; 2. SINTAXIS LOGICA (El Guardian del Sentido)
;;; ==========================================

(defclass logische-regel (node)
  ((struktur :initarg :struktur :reader regla-struktur)
   (validador :initarg :validador :reader regla-validador))) ; Una funcion/closure Lisp

(defun tiene-sentido-p (sachverhalt reglas welt)
  "Verifica si un estado de cosas no viola la sintaxis logica (Evita sinsentidos)."
  (let ((regel (gethash (struktur sachverhalt) reglas)))
    (if regel
        ;; Llama al closure validador pasandole los objetos y el mundo
        (funcall (regla-validador regel) (objekte sachverhalt) welt)
        t))) ;; Si no hay regla que lo prohiba, asumimos que tiene sentido estructural.

;;; ==========================================
;;; 3. LA MAQUINA DE LA VERDAD (Motor de Inferencia)
;;; ==========================================

(defun truth-of (sachverhalt welt)
  "Tractatus 4.25: Una proposicion elemental es verdadera si el Sachverhalt existe."
  (let ((hash-sv (calculate-merkle-hash sachverhalt)))
    ;; Gracias al Hashing Semantico, buscar la verdad es O(1)
    (if (gethash hash-sv (welt-tatsachen welt))
        t
        nil)))

(defun assert-tatsache (sachverhalt welt reglas)
  "El acto de asimilacion: Intenta cristalizar un Sachverhalt como un Hecho en el Mundo."
  (if (tiene-sentido-p sachverhalt reglas welt)
      (let* ((hash-sv (calculate-merkle-hash sachverhalt))
             (nuevo-hecho (make-instance 'tatsache :von sachverhalt :hash-id hash-sv)))
        ;; Indexa el hecho en el mundo
        (setf (gethash hash-sv (welt-tatsachen welt)) nuevo-hecho)
        nuevo-hecho)
      ;; Si falla la sintaxis logica, el sistema vomita la traza
      (error 'sinsentido-error
             :format-control "Violacion de sintaxis: ~A no tiene sentido en este mundo."
             :format-arguments (list sachverhalt))))

;;; ==========================================
;;; 4. EL MOTOR DE PROYECCION (El Lector usando Macros)
;;; ==========================================
;; Esta macro permite compilar "Templates" de SLDB en funciones Lisp ultrarrapidas
;; que inyectan el conocimiento en el Grafo al leer los textos.

(defmacro def-template (id &key match trazas)
  "Compila un patron de texto en una funcion que inyecta trazas logicas al Welt."
  (let ((func-name (intern (concatenate 'string "APPLY-TEMPLATE-" (symbol-name id)))))
    `(defun ,func-name (texto welt reglas nlp-bridge)
       ;; 1. Usar el NLP (o el LLM transpilador) para extraer bindings ("?x = auto")
       (let ((bindings (extract-variables ,match texto nlp-bridge)))
         ;; 2. Generar y evaluar cada traza (S-expression)
         (dolist (traza ',trazas)
           (let ((nuevo-sv (instantiate-sexp traza bindings welt)))
             ;; 3. Afirmar el hecho en el mundo
             (assert-tatsache nuevo-sv welt reglas)))))))

;;;; tractatus-ring.lisp
;;;; The Assimilation Ring (SLDB -> NLP -> Indexer -> Core)

(defpackage #:tractatus-ring
  (:use #:cl))
(in-package #:tractatus-ring)

(defparameter *welt-sign-index* (make-hash-table :test 'equal))
(defparameter *welt-taxonomy-children-index* (make-hash-table :test 'equal))

(defun ensure-taxonomy-children-index (welt)
  (or (gethash welt *welt-taxonomy-children-index*)
      (setf (gethash welt *welt-taxonomy-children-index*)
            (make-hash-table :test 'equal))))

(defun ensure-sign-index (welt)
  (or (gethash welt *welt-sign-index*)
      (setf (gethash welt *welt-sign-index*)
            (make-hash-table :test 'equal))))

(defun register-sign-binding (signo-string object-id welt)
  (let* ((index (ensure-sign-index welt))
         (bucket (gethash signo-string index)))
    (pushnew object-id bucket :test #'equal)
    (setf (gethash signo-string index) bucket)
    object-id))

(defun resolve-name (signo-string welt &key instancia-de)
  "Resolve polysemy in the current world and return a logical object id."
  (let* ((index (ensure-sign-index welt))
         (nombres-posibles (gethash signo-string index)))
    (if nombres-posibles
        (first nombres-posibles)
        (let ((nuevo-id (format nil "obj-~A"
                                (tractatus-core::calculate-merkle-hash
                                 (list 'name signo-string
                                       (tractatus-core::hash-id welt))))))
          (register-sign-binding signo-string nuevo-id welt)
          (when instancia-de
            (tractatus-core::register-gegenstand welt nuevo-id :instancia-de instancia-de))
          nuevo-id))))

(defun index-jerarquia (hijo padre welt)
  "Maintain a parent -> children taxonomy index alongside the core registry."
  (let* ((index (ensure-taxonomy-children-index welt))
         (bucket (gethash padre index)))
    (pushnew hijo bucket :test #'equal)
    (setf (gethash padre index) bucket)
    hijo))

(defun traza-propiedad (sujeto objeto estructura)
  (list 'sachverhalt :objekte (list sujeto objeto) :struktur estructura))

(defun text-to-candidate-sexps (texto welt)
  "Call the external NLP bridge and receive candidate logical traces.
This placeholder keeps the ring testable without the external Python system."
  (declare (ignore welt))
  (format t "~%[NLP-BRIDGE] Translating candidate text: ~S~%" texto)
  (cond
    ((search "rojo" texto :test #'char-equal)
     (list (traza-propiedad "auto" "rojo" :has-color)))
    ((search "azul" texto :test #'char-equal)
     (list (traza-propiedad "auto" "azul" :has-color)))
    (t nil)))

(defun extraer-campos-de-json (document-json)
  "Extract textual fields from a minimal plist or alist document payload."
  (cond
    ((and (listp document-json) (keywordp (first document-json)))
     (or (getf document-json :fields) '()))
    ((and (listp document-json) (consp (first document-json)))
     (or (cdr (assoc :fields document-json)) '()))
    (t '())))

(defun candidate-objekte (traza)
  (getf (rest traza) :objekte))

(defun candidate-struktur (traza)
  (getf (rest traza) :struktur))

(defun process-sldb-document (document-json welt reglas)
  "Orchestrate one SLDB payload into the core truth machine."
  (tractatus-worlds::assert-ingestion-target welt)
  (format t "~%[SLDB] Processing document in world: ~A~%"
          (tractatus-core::hash-id welt))
  (dolist (campo (extraer-campos-de-json document-json))
    (dolist (traza (text-to-candidate-sexps campo welt))
      (let* ((objetos (candidate-objekte traza))
             (signo-sujeto (first objetos))
             (signo-objeto (second objetos))
             (verbo (candidate-struktur traza))
             (nodo-sujeto (resolve-name signo-sujeto welt))
             (nodo-objeto (resolve-name signo-objeto welt))
             (sv-real (make-instance 'tractatus-core::sachverhalt
                                     :objekte (list nodo-sujeto nodo-objeto)
                                     :struktur verbo)))
        (handler-case
            (let ((hecho (tractatus-core::assert-tatsache sv-real welt reglas)))
              (format t "[CORE] Accepted. Inserted fact hash: ~A~%"
                      (tractatus-core::hash-id hecho)))
          (tractatus-core::sinsentido-error (e)
            (format t "[CORE] Rejected. Invalid text or hallucinated trace: ~A~%" e)))))))

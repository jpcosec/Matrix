;;;; tractatus-periphery.lisp
;;;; Peripheral utilities and test support around the core.

(in-package #:tractatus-core)

(define-condition sinsentido-error (error)
  ((format-control :initarg :format-control :reader sinsentido-format-control)
   (format-arguments :initarg :format-arguments :initform nil :reader sinsentido-format-arguments))
  (:report (lambda (condition stream)
             (apply #'format stream
                    (sinsentido-format-control condition)
                    (sinsentido-format-arguments condition)))))

(defun canonical-value (value)
  (typecase value
    (cons
     (mapcar #'canonical-value value))
    (symbol
     (list :symbol (symbol-name value)))
    (string
     (list :string value))
    (t
     value)))

(defun canonical-node-form (node)
  (typecase node
    (begriff
     (list :begriff (subclase-de node)))
    (gegenstand
     (list :gegenstand (instancia-de node)))
    (sachverhalt
     (list :sachverhalt
           (canonical-value (struktur node))
           (canonical-value (objekte node))))
    (tatsache
     (list :tatsache (calculate-merkle-hash (von node))))
    (welt
     (list :welt (hash-table-count (welt-tatsachen node))))
    (t
     (canonical-value node))))

(defun calculate-merkle-hash (node)
  "Simplified content hash for in-memory identity and tests."
  (format nil "~36R" (abs (sxhash (canonical-node-form node)))))

(defun register-begriff (welt begriff-id &key subclase-de)
  (setf (gethash begriff-id (welt-taxonomia welt)) subclase-de)
  begriff-id)

(defun register-gegenstand (welt gegenstand-id &key instancia-de)
  (setf (gethash gegenstand-id (welt-nombres welt)) instancia-de)
  gegenstand-id)

(defun concept-isa-p (concept target welt)
  (cond
    ((null concept) nil)
    ((eql concept target) t)
    (t (concept-isa-p (gethash concept (welt-taxonomia welt)) target welt))))

(defun instance-of-p (gegenstand-id target-begriff welt)
  (let ((instancia (gethash gegenstand-id (welt-nombres welt))))
    (concept-isa-p instancia target-begriff welt)))

(defun extract-variables (match texto nlp-bridge)
  (declare (ignore match texto nlp-bridge))
  (error "extract-variables is not implemented yet."))

(defun instantiate-sexp (traza bindings welt)
  (declare (ignore traza bindings welt))
  (error "instantiate-sexp is not implemented yet."))

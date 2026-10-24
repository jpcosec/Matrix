;;;; tractatus-axes.lisp
;;;; Contextual bit axes for local world indexing.

(defpackage #:tractatus-axes
  (:use #:cl))
(in-package #:tractatus-axes)

(defparameter *welt-axes* (make-hash-table :test 'eq))
(defparameter *welt-axis-projections* (make-hash-table :test 'eq))

(defun ensure-axis-store (welt)
  (or (gethash welt *welt-axes*)
      (setf (gethash welt *welt-axes*)
            (make-hash-table :test 'equal))))

(defun ensure-projection-store (welt)
  (or (gethash welt *welt-axis-projections*)
      (setf (gethash welt *welt-axis-projections*)
            (make-hash-table :test 'equal))))

(defun axis-values (axis-name welt)
  (let ((axis (gethash axis-name (ensure-axis-store welt))))
    (when axis
      (copy-list axis))))

(defun define-axis (welt axis-name values)
  (setf (gethash axis-name (ensure-axis-store welt))
        (remove-duplicates (copy-list values) :test #'equal))
  axis-name)

(defun ensure-axis-value (welt axis-name value)
  (let* ((store (ensure-axis-store welt))
         (values (copy-list (gethash axis-name store))))
    (unless (member value values :test #'equal)
      (setf values (append values (list value)))
      (setf (gethash axis-name store) values))
    value))

(defun axis-bitstring (welt axis-name value)
  (let* ((values (or (axis-values axis-name welt)
                     (error "Unknown axis ~A in world ~A"
                            axis-name
                            (tractatus-core::hash-id welt))))
         (buffer (make-string-output-stream))
         (matched nil))
    (dolist (candidate values)
      (if (equal candidate value)
          (progn
            (write-char #\1 buffer)
            (setf matched t))
          (write-char #\0 buffer)))
    (unless matched
      (error "Unknown axis value ~A for axis ~A" value axis-name))
    (get-output-stream-string buffer)))

(defun project-concept (welt concept-id axis-name value)
  (ensure-axis-value welt axis-name value)
  (let* ((store (ensure-projection-store welt))
         (concept-entry (or (gethash concept-id store)
                            (setf (gethash concept-id store)
                                  (make-hash-table :test 'equal)))))
    (setf (gethash axis-name concept-entry) value)
    concept-id))

(defun concept-axis-value (welt concept-id axis-name)
  (let ((concept-entry (gethash concept-id (ensure-projection-store welt))))
    (when concept-entry
      (gethash axis-name concept-entry))))

(defun concept-axis-bitstring (welt concept-id axis-name)
  (let ((value (concept-axis-value welt concept-id axis-name)))
    (when value
      (axis-bitstring welt axis-name value))))

(defun concept-signature (welt concept-id &key axis-order)
  (let* ((axes (or axis-order
                   (sort (loop for key being the hash-keys of (ensure-axis-store welt)
                               collect key)
                         #'string< :key #'string)))
         (buffer (make-string-output-stream)))
    (dolist (axis-name axes)
      (let ((bitstring (concept-axis-bitstring welt concept-id axis-name)))
        (when bitstring
          (princ bitstring buffer))))
    (get-output-stream-string buffer)))

(defun context-mask (welt active-axes)
  (let ((all-axes (sort (loop for key being the hash-keys of (ensure-axis-store welt)
                              collect key)
                        #'string< :key #'string))
        (buffer (make-string-output-stream)))
    (dolist (axis-name all-axes)
      (let ((width (length (axis-values axis-name welt))))
        (dotimes (_ width)
          (write-char (if (member axis-name active-axes :test #'equal) #\1 #\0)
                      buffer))))
    (get-output-stream-string buffer)))

(defun apply-context-mask (signature mask)
  (let ((buffer (make-string-output-stream)))
    (loop for sig across signature
          for bit across mask do
      (write-char (if (char= bit #\1) sig #\0) buffer))
    (get-output-stream-string buffer)))

(defun contextual-signature (welt concept-id active-axes)
  (let ((signature (concept-signature welt concept-id))
        (mask (context-mask welt active-axes)))
    (apply-context-mask signature mask)))

(defun matching-concepts (welt concept-id active-axes)
  (let* ((target (contextual-signature welt concept-id active-axes))
         (store (ensure-projection-store welt))
         (matches '()))
    (maphash (lambda (candidate-id _)
               (declare (ignore _))
               (when (string= target (contextual-signature welt candidate-id active-axes))
                 (push candidate-id matches)))
             store)
    (nreverse matches)))

(defun export-axis-state (welt)
  (let ((axes '())
        (projections '()))
    (maphash (lambda (axis-name values)
               (push (list :axis axis-name :values (copy-list values)) axes))
             (ensure-axis-store welt))
    (maphash (lambda (concept-id axis-map)
               (let ((entry '()))
                 (maphash (lambda (axis-name value)
                            (push (list axis-name value) entry))
                          axis-map)
                 (push (list :concept concept-id :axes (nreverse entry)) projections)))
             (ensure-projection-store welt))
    (list :axes (nreverse axes)
          :projections (nreverse projections))))

(defun import-axis-state (welt axis-state)
  (clrhash (ensure-axis-store welt))
  (clrhash (ensure-projection-store welt))
  (dolist (axis (getf axis-state :axes))
    (define-axis welt (getf axis :axis) (getf axis :values)))
  (dolist (projection (getf axis-state :projections))
    (dolist (axis-entry (getf projection :axes))
      (project-concept welt
                       (getf projection :concept)
                       (first axis-entry)
                       (second axis-entry))))
  welt)

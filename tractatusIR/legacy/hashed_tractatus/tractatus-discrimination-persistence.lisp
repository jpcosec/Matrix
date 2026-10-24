;;;; tractatus-discrimination-persistence.lisp
;;;; Persistence helpers for contextual discrimination state.

(defpackage #:tractatus-discrimination-persistence
  (:use #:cl))
(in-package #:tractatus-discrimination-persistence)

(defun write-sexp-file (path object)
  (ensure-directories-exist path)
  (with-open-file (stream path
                          :direction :output
                          :if-exists :supersede
                          :if-does-not-exist :create)
    (let ((*print-pretty* t))
      (write object :stream stream)
      (terpri stream))))

(defun read-sexp-file (path)
  (with-open-file (stream path :direction :input)
    (let ((*read-eval* nil))
      (read stream nil nil))))

(defun export-discrimination-state (welt)
  (let ((dimensions '())
        (contexts '())
        (projections '()))
    (maphash (lambda (dimension-id payload)
               (declare (ignore dimension-id))
               (push (copy-tree payload) dimensions))
             (tractatus-discrimination::ensure-dimension-store welt))
    (maphash (lambda (context-id payload)
               (declare (ignore context-id))
               (push (copy-tree payload) contexts))
             (tractatus-discrimination::ensure-context-store welt))
    (maphash (lambda (context-id concept-table)
               (let ((concepts '()))
                 (maphash (lambda (concept-id dimension-table)
                            (let ((pairs '()))
                              (maphash (lambda (dimension-id value)
                                         (push (list dimension-id value) pairs))
                                       dimension-table)
                              (push (list :concept concept-id :values (nreverse pairs)) concepts)))
                          concept-table)
                 (push (list :context context-id :concepts (nreverse concepts)) projections)))
             (tractatus-discrimination::ensure-projection-store welt))
    (list :welt-id (tractatus-core::hash-id welt)
          :dimensions (nreverse dimensions)
          :contexts (nreverse contexts)
          :projections (nreverse projections))))

(defun import-discrimination-state (welt state)
  (unless (string= (tractatus-core::hash-id welt)
                   (getf state :welt-id))
    (error "Discrimination state belongs to world ~A, not ~A"
           (getf state :welt-id)
           (tractatus-core::hash-id welt)))
  (clrhash (tractatus-discrimination::ensure-dimension-store welt))
  (clrhash (tractatus-discrimination::ensure-context-store welt))
  (clrhash (tractatus-discrimination::ensure-projection-store welt))
  (dolist (dimension (getf state :dimensions))
    (tractatus-discrimination::define-dimension
     welt
     (getf dimension :id)
     (getf dimension :values)
     :question (getf dimension :question)
     :type (getf dimension :type)))
  (dolist (context (getf state :contexts))
    (tractatus-discrimination::define-context
     welt
     (getf context :id)
     (getf context :universe)
     (getf context :task)
     (getf context :tree)))
  (dolist (context-entry (getf state :projections))
    (dolist (concept-entry (getf context-entry :concepts))
      (dolist (value-entry (getf concept-entry :values))
        (tractatus-discrimination::project-concept
         welt
         (getf context-entry :context)
         (getf concept-entry :concept)
         (first value-entry)
         (second value-entry)))))
  welt)

(defun save-discrimination-state (welt directory)
  (let ((path (merge-pathnames "discrimination.sexp" directory)))
    (write-sexp-file path (export-discrimination-state welt))
    path))

(defun load-discrimination-state (welt path)
  (import-discrimination-state welt (read-sexp-file path)))

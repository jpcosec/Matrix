;;;; tractatus-persistence.lisp
;;;; Local world snapshot persistence with compressed axis state.

(defpackage #:tractatus-persistence
  (:use #:cl))
(in-package #:tractatus-persistence)

(defun write-sexp-file (path object)
  (ensure-directories-exist path)
  (with-open-file (stream path
                          :direction :output
                          :if-exists :supersede
                          :if-does-not-exist :create)
    (let ((*print-pretty* t)
          (*print-circle* nil))
      (write object :stream stream)
      (terpri stream))))

(defun read-sexp-file (path)
  (with-open-file (stream path :direction :input)
    (read stream nil nil)))

(defun hash-table-alist (table)
  (let ((result '()))
    (maphash (lambda (key value)
               (push (cons key value) result))
             table)
    (nreverse result)))

(defun export-facts (welt)
  (let ((facts '()))
    (maphash (lambda (fact-hash fact)
               (let ((sv (tractatus-core::von fact)))
                 (push (list :fact fact-hash
                             :struktur (tractatus-core::struktur sv)
                             :objekte (copy-list (tractatus-core::objekte sv)))
                       facts)))
             (tractatus-core::welt-tatsachen welt))
    (nreverse facts)))

(defun export-sign-index (welt)
  (let ((index (gethash welt tractatus-ring::*welt-sign-index*)))
    (if index
        (hash-table-alist index)
        '())))

(defun export-taxonomy (welt)
  (hash-table-alist (tractatus-core::welt-taxonomia welt)))

(defun export-world-summary (welt)
  (let ((facts (export-facts welt))
        (signs (export-sign-index welt))
        (axes (tractatus-axes::export-axis-state welt)))
    (list :welt-id (tractatus-core::hash-id welt)
          :fact-count (length facts)
          :sign-count (length signs)
          :axis-count (length (getf axes :axes))
          :facts facts
          :signs signs
          :axes axes)))

(defun save-welt-snapshot (welt directory)
  (let* ((welt-id (tractatus-core::hash-id welt))
         (base (merge-pathnames
                (make-pathname :directory `(:relative ,(tractatus-worlds::normalize-welt-segment welt-id)))
                directory)))
    (write-sexp-file (merge-pathnames "welt.sexp" base)
                     (list :welt-id welt-id
                           :parent (tractatus-worlds::infer-parent-welt-id welt-id)
                           :kind (tractatus-worlds::welt-kind-from-id welt-id)))
    (write-sexp-file (merge-pathnames "facts.sexp" base) (export-facts welt))
    (write-sexp-file (merge-pathnames "signs.sexp" base) (export-sign-index welt))
    (write-sexp-file (merge-pathnames "taxonomy.sexp" base) (export-taxonomy welt))
    (write-sexp-file (merge-pathnames "axes.sexp" base) (tractatus-axes::export-axis-state welt))
    (write-sexp-file (merge-pathnames "bundle.sexp" base) (export-world-summary welt))
    base))

(defun import-sign-index (welt sign-alist)
  (dolist (entry sign-alist)
    (dolist (object-id (cdr entry))
      (tractatus-ring::register-sign-binding (car entry) object-id welt)))
  welt)

(defun import-taxonomy (welt taxonomy-alist)
  (clrhash (tractatus-core::welt-taxonomia welt))
  (dolist (entry taxonomy-alist)
    (setf (gethash (car entry) (tractatus-core::welt-taxonomia welt))
          (cdr entry)))
  welt)

(defun import-facts (welt facts)
  (clrhash (tractatus-core::welt-tatsachen welt))
  (dolist (fact facts)
    (let* ((sv (make-instance 'tractatus-core::sachverhalt
                              :hash-id (getf fact :fact)
                              :objekte (copy-list (getf fact :objekte))
                              :struktur (getf fact :struktur)))
           (tf (make-instance 'tractatus-core::tatsache
                              :hash-id (getf fact :fact)
                              :von sv)))
      (setf (gethash (getf fact :fact) (tractatus-core::welt-tatsachen welt)) tf)))
  welt)

(defun load-welt-snapshot (directory)
  (let* ((welt-metadata (read-sexp-file (merge-pathnames "welt.sexp" directory)))
         (welt (tractatus-worlds::make-welt :id (getf welt-metadata :welt-id))))
    (import-facts welt (read-sexp-file (merge-pathnames "facts.sexp" directory)))
    (import-sign-index welt (read-sexp-file (merge-pathnames "signs.sexp" directory)))
    (import-taxonomy welt (read-sexp-file (merge-pathnames "taxonomy.sexp" directory)))
    (tractatus-axes::import-axis-state welt (read-sexp-file (merge-pathnames "axes.sexp" directory)))
    welt))

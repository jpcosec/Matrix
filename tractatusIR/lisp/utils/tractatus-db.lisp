;;;; tractatus-db.lisp
;;;; Persistence layer for Tractatus Lisp implementation
;;;; Uses single source of truth hash tables from other modules
;;;; No PostgreSQL dependency - hash tables + file serialization only

(defpackage :tractatus-db
  (:use :cl :tractatus-signatures :tractatus-semantics
            :tractatus-discrimination :tractatus-update
            :tractatus-selection :tractatus-security
            :tractatus-inference :tractatus-versioning)
  (:export
   #:save-all-to-file
   #:load-all-from-file
   #:clear-all
   #:print-status))

(in-package :tractatus-db)

;;; ============================================================
;;; Helper: Convert hash table to alist for serialization
;;; ============================================================

(defun hash-table-to-alist (ht)
  "Convert hash table to alist for serialization."
  (let ((result nil))
    (maphash #'(lambda (k v) (push (cons k v) result)) ht)
    result))

(defun alist-to-hash-table (alist ht)
  "Load alist into hash table (clears existing data)."
  (clrhash ht)
  (dolist (pair alist)
    (setf (gethash (car pair) ht) (cdr pair)))
  ht)

;;; ============================================================
;;; Persistence: Save all state to file
;;; ============================================================

(defun save-all-to-file (file-path)
  "Serialize all runtime hash tables to a single file.
   Uses the actual hash tables from each module (single source of truth)."
  (with-open-file (out file-path
                   :direction :output
                   :if-exists :supersede
                   :if-does-not-exist :create)
    (let ((data
           (list
            (cons :concepts (hash-table-to-alist tractatus-update::*concepts*))
            (cons :facts (hash-table-to-alist tractatus-update::*facts*))
            (cons :dimensions (hash-table-to-alist tractatus-update::*dimensions*))
            (cons :contexts (hash-table-to-alist tractatus-update::*contexts*))
            (cons :indices (hash-table-to-alist tractatus-update::*indices*))
            (cons :universes (hash-table-to-alist tractatus-semantics::*universes*))
            (cons :valid-masks (hash-table-to-alist tractatus-signatures::*valid-masks*))
            (cons :sense-masks (hash-table-to-alist tractatus-signatures::*sense-masks*))
            (cons :discriminative-masks (hash-table-to-alist tractatus-signatures::*discriminative-masks*))
            (cons :observed-masks (hash-table-to-alist tractatus-signatures::*observed-masks*))
            (cons :rules (hash-table-to-alist tractatus-inference::*rules*))
            (cons :context-versions (hash-table-to-alist tractatus-versioning::*context-versions*))
            (cons :current-versions (hash-table-to-alist tractatus-versioning::*current-versions*))
            (cons :dimension-costs (hash-table-to-alist tractatus-selection::*dimension-costs*))
            (cons :dimension-uncertainty (hash-table-to-alist tractatus-selection::*dimension-uncertainty*)))))
      (print data out)))
  (format t "✓ State saved to ~a~%" file-path)
  t)

;;; ============================================================
;;; Persistence: Load all state from file
;;; ============================================================

(defun load-all-from-file (file-path)
  "Load all state from file into the runtime hash tables."
  (with-open-file (in file-path
                   :direction :input
                   :if-does-not-exist nil)
    (unless in
      (format t "✗ File not found: ~a~%" file-path)
      (return-from load-all-from-file nil))
    (let ((data (read in nil nil)))
      (unless data
        (format t "✗ Error reading data from ~a~%" file-path)
        (return-from load-all-from-file nil))
      (dolist (pair data)
        (let ((key (car pair))
              (value (cdr pair)))
          (case key
            (:concepts (alist-to-hash-table value tractatus-update::*concepts*))
            (:facts (alist-to-hash-table value tractatus-update::*facts*))
            (:dimensions (alist-to-hash-table value tractatus-update::*dimensions*))
            (:contexts (alist-to-hash-table value tractatus-update::*contexts*))
            (:indices (alist-to-hash-table value tractatus-update::*indices*))
            (:universes (alist-to-hash-table value tractatus-semantics::*universes*))
            (:valid-masks (alist-to-hash-table value tractatus-signatures::*valid-masks*))
            (:sense-masks (alist-to-hash-table value tractatus-signatures::*sense-masks*))
            (:discriminative-masks (alist-to-hash-table value tractatus-signatures::*discriminative-masks*))
            (:observed-masks (alist-to-hash-table value tractatus-signatures::*observed-masks*))
            (:rules (alist-to-hash-table value tractatus-inference::*rules*))
            (:context-versions (alist-to-hash-table value tractatus-versioning::*context-versions*))
            (:current-versions (alist-to-hash-table value tractatus-versioning::*current-versions*))
            (:dimension-costs (alist-to-hash-table value tractatus-selection::*dimension-costs*))
            (:dimension-uncertainty (alist-to-hash-table value tractatus-selection::*dimension-uncertainty*)))))))
    (format t "✓ State loaded from ~a~%" file-path))
  t)

;;; ============================================================
;;; Utility: Clear all state (reset to empty)
;;; ============================================================

(defun clear-all ()
  "Clear all runtime hash tables (reset to empty state)."
  (clrhash tractatus-update::*concepts*)
  (clrhash tractatus-update::*facts*)
  (clrhash tractatus-update::*dimensions*)
  (clrhash tractatus-update::*contexts*)
  (clrhash tractatus-update::*indices*)
  (clrhash tractatus-semantics::*universes*)
  (clrhash tractatus-signatures::*valid-masks*)
  (clrhash tractatus-signatures::*sense-masks*)
  (clrhash tractatus-signatures::*discriminative-masks*)
  (clrhash tractatus-signatures::*observed-masks*)
  (clrhash tractatus-inference::*rules*)
  (clrhash tractatus-versioning::*context-versions*)
  (clrhash tractatus-versioning::*current-versions*)
  (clrhash tractatus-selection::*dimension-costs*)
  (clrhash tractatus-selection::*dimension-uncertainty*)
  (format t "✓ All state cleared~%")
  t)

;;; ============================================================
;;; Status: Print current state counts
;;; ============================================================

(defun print-status ()
  "Print status of all runtime hash tables."
  (format t "~%=== Tractatus Runtime State ===~%")
  (format t "Concepts: ~a~%" (hash-table-count tractatus-update::*concepts*))
  (format t "Facts: ~a~%" (hash-table-count tractatus-update::*facts*))
  (format t "Dimensions: ~a~%" (hash-table-count tractatus-update::*dimensions*))
  (format t "Contexts: ~a~%" (hash-table-count tractatus-update::*contexts*))
  (format t "Indices: ~a~%" (hash-table-count tractatus-update::*indices*))
  (format t "Universes: ~a~%" (hash-table-count tractatus-semantics::*universes*))
  (format t "Valid masks: ~a~%" (hash-table-count tractatus-signatures::*valid-masks*))
  (format t "Sense masks: ~a~%" (hash-table-count tractatus-signatures::*sense-masks*))
  (format t "Discriminative masks: ~a~%" (hash-table-count tractatus-signatures::*discriminative-masks*))
  (format t "Observed masks: ~a~%" (hash-table-count tractatus-signatures::*observed-masks*))
  (format t "Rules: ~a~%" (hash-table-count tractatus-inference::*rules*))
  (format t "Context versions: ~a~%" (hash-table-count tractatus-versioning::*context-versions*))
  (format t "Current versions: ~a~%" (hash-table-count tractatus-versioning::*current-versions*))
  (format t "Dimension costs: ~a~%" (hash-table-count tractatus-selection::*dimension-costs*))
  (format t "Dimension uncertainty: ~a~%" (hash-table-count tractatus-selection::*dimension-uncertainty*))
  t)

;;; ============================================================
;;; Backward compatibility: init-db (now a no-op, returns :memory)
;;; ============================================================

(defun init-db (&key (type :memory))
  "Initialize database (backward compatible).
   Now just clears state and returns :memory (no PostgreSQL)."
  (declare (ignore type))
  (clear-all)
  (format t "✓ DB initialized (hash tables, in-memory)~%")
  :memory)

;;; ============================================================
;;; Demo helper: Quick save/load test
;;; ============================================================

(defun test-persistence ()
  "Quick test of persistence (save then load)."
  (format t "~%=== Testing Persistence ===~%")
  (print-status)
  (save-all-to-file "/tmp/tractatus_test_save.lisp")
  (clear-all)
  (format t "~%After clear:~%")
  (print-status)
  (load-all-from-file "/tmp/tractatus_test_save.lisp")
  (format t "~%After reload:~%")
  (print-status))

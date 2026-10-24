;;;; tractatus-versioning.lisp
;;;; Context versioning: track changes to contexts, dictionaries, signatures
;;;; Implements Turn 44 item 10: versioning of contexts

(defpackage :tractatus-versioning
  (:use :cl :tractatus-signatures)
  (:export
   #:defcontext
   #:update-context-version
   #:get-context-version
   #:rollback-context
   #:migrate-signatures
   #:context-versions
   #:current-version
   #:version-difference
   #:rebuild-all-signatures))

(in-package :tractatus-versioning)

;;; ============================================================
;;; Version Structures
;;; ============================================================

(defstruct context-version
  "A version of a context with its configuration."
  (version 1 :type integer)
  (parent-version nil :type (or null integer))
  (context-id nil :type symbol)
  (dimensions nil :type list)
  (bit-dictionary nil :type list)
  (sense-mask nil :type (or null mask-signature))
  (valid-mask nil :type (or null mask-signature))
  (discriminative-mask nil :type (or null mask-signature))
  (observed-mask nil :type (or null mask-signature))
  (universe nil :type list)
  (changes nil :type list)  ; list of change descriptions
  (timestamp nil :type (or null string)))

(defvar *context-versions* (make-hash-table :test 'eq)
  "Maps context-id to list of versions (newest first)")

(defvar *current-versions* (make-hash-table :test 'eq)
  "Maps context-id to current version number")

;;; ============================================================
;;; Define Context with Versioning
;;; ============================================================

(defun defcontext (context-id &key (dimensions nil) (universe nil) (bit-dictionary nil))
  "Define a new context, creating version 1.
   Returns context-version."
  (let ((ctx-v1 (make-context-version
                 :version 1
                 :context-id context-id
                 :dimensions dimensions
                 :bit-dictionary bit-dictionary
                 :universe universe
                 :timestamp (get-current-timestamp))))
    (setf (gethash context-id *context-versions*) (list ctx-v1))
    (setf (gethash context-id *current-versions*) 1)
    ;; Also set in tractatus-update
    (setf (gethash context-id *contexts*) (list :dimensions dimensions :universe universe))
    (when universe
      (setf (universe context-id) universe))
    ctx-v1))

;;; ============================================================
;;; Update Context Version
;;; ============================================================

(defun update-context-version (context-id &key (add-dimensions nil)
                                              (remove-dimensions nil)
                                              (add-values nil)  ; (dim-id . values)
                                              (update-mask nil) ; (mask-type . new-mask)
                                              (new-universe nil))
  "Create a new version of context.
   Returns new context-version."
  (let* ((current-ver (get-current-version context-id))
         (current-ctx (get-context-version context-id current-ver))
         (new-ver (1+ (or current-ver 0)))
         (old-dims (when current-ctx (context-version-dimensions current-ctx)))
         (new-dims (copy-list old-dims))
         (changes nil))
    ;; Apply changes
    (dolist (dim add-dimensions)
      (pushnew dim new-dims)
      (push (format nil "added_dimension: ~a" dim) changes))
    (dolist (dim remove-dimensions)
      (setf new-dims (remove dim new-dims))
      (push (format nil "removed_dimension: ~a" dim) changes))
    (dolist (av add-values)
      (push (format nil "added_value: ~a to ~a" (cdr av) (car av)) changes))
    (when new-universe
      (setf (context-version-universe current-ctx) new-universe)
      (push "updated_universe" changes))
    ;; Create new version
    (let ((new-ctx (make-context-version
                    :version new-ver
                    :parent-version current-ver
                    :context-id context-id
                    :dimensions new-dims
                    :bit-dictionary (when current-ctx
                                      (copy-list (context-version-bit-dictionary current-ctx)))
                    :sense-mask (when current-ctx (context-version-sense-mask current-ctx))
                    :valid-mask (when current-ctx (context-version-valid-mask current-ctx))
                    :discriminative-mask (when current-ctx (context-version-discriminative-mask current-ctx))
                    :observed-mask (when current-ctx (context-version-observed-mask current-ctx))
                    :universe (or new-universe
                                 (when current-ctx (context-version-universe current-ctx)))
                    :changes changes
                    :timestamp (get-current-timestamp))))
      ;; Update version lists
      (push new-ctx (gethash context-id *context-versions*))
      (setf (gethash context-id *current-versions*) new-ver)
      ;; Rebuild dependent structures
      (rebuild-for-version new-ctx)
      new-ctx)))

;;; ============================================================
;;; Get Context Version
;;; ============================================================

(defun get-context-version (context-id &optional (version nil))
  "Get specific version of context.
   If version is nil, returns current version."
  (let ((versions (gethash context-id *context-versions*))
        (target-ver (or version (get-current-version context-id))))
    (find-if #'(lambda (v) (= (context-version-version v) target-ver))
             versions)))

(defun get-current-version (context-id)
  (gethash context-id *current-versions*))

;;; ============================================================
;;; Rollback Context
;;; ============================================================

(defun rollback-context (context-id &optional (target-version nil))
  "Rollback to a previous version.
   If target-version is nil, rollback to parent of current."
  (let ((current-ver (get-current-version context-id)))
    (unless current-ver
      (return-from rollback-context nil))
    (let* ((target (or target-version (1- current-ver)))
           (target-ctx (get-context-version context-id target)))
      (unless target-ctx
        (return-from rollback-context nil))
      ;; Remove newer versions
      (let ((versions (gethash context-id *context-versions*)))
        (setf (gethash context-id *context-versions*)
              (remove-if #'(lambda (v) (> (context-version-version v) target))
                         versions)))
      (setf (gethash context-id *current-versions*) target)
      ;; Rebuild
      (rebuild-for-version target-ctx)
      target-ctx)))

;;; ============================================================
;;; Migrate Old Signatures
;;; Signatures from old versions may become unreadable
;;; ============================================================

(defun migrate-signatures (context-id &key (from-version nil) (to-version nil))
  "Migrate signatures from one version to another.
   Returns count of migrated signatures."
  (let ((from-ver (or from-version (1- (get-current-version context-id))))
        (to-ver (or to-version (get-current-version context-id)))
        (count 0))
    (declare (ignore from-ver to-ver))
    ;; Would iterate over all concept-signatures and rebuild
    ;; based on new bit-dictionary and dimensions
    (loop for concept-id being each hash-key of *concepts*
          do (incf count)
             (rebuild-signature concept-id context-id))
    count))

;;; ============================================================
;;; Rebuild All Signatures
;;; ============================================================

(defun rebuild-all-signatures (context-id)
  "Rebuild all signatures in context after version change."
  (loop for concept-id being each hash-key of *concepts*
        do (rebuild-signature concept-id context-id))
  t)

;;; ============================================================
;;; Helper Functions
;;; ============================================================

(defun rebuild-for-version (ctx)
  "Rebuild system state for a context version."
  (let ((context-id (context-version-context-id ctx)))
    ;; Update tractatus-update context
    (setf (gethash context-id *contexts*)
          (list :dimensions (context-version-dimensions ctx)
                :universe (context-version-universe ctx)))
    ;; Update universe
    (when (context-version-universe ctx)
      (setf (universe context-id) (context-version-universe ctx)))
    ;; Update masks if available
    (when (context-version-sense-mask ctx)
      (setf (sense-mask context-id) (context-version-sense-mask ctx)))
    (when (context-version-valid-mask ctx)
      (setf (valid-mask context-id) (context-version-valid-mask ctx)))
    ;; Rebuild signatures
    (rebuild-all-signatures context-id)))

(defun get-current-timestamp ()
  "Get current timestamp string."
  (multiple-value-bind (sec min hour day month year) (get-decoded-time)
    (format nil "~4,'0d-~2,'0d-~2,'0dT~2,'0d:~2,'0d:~2,'0d"
            year month day hour min sec)))

;;; ============================================================
;;; Version Info
;;; ============================================================

(defun context-versions (context-id)
  "List all versions of a context."
  (let ((versions (gethash context-id *context-versions*)))
    (mapcar #'(lambda (v)
                (list :version (context-version-version v)
                      :parent (context-version-parent-version v)
                      :dimensions (context-version-dimensions v)
                      :changes (context-version-changes v)
                      :timestamp (context-version-timestamp v)))
            versions)))

(defun version-difference (context-id v1 v2)
  "Compare two versions and return differences."
  (let ((ctx1 (get-context-version context-id v1))
        (ctx2 (get-context-version context-id v2)))
    (unless (and ctx1 ctx2)
      (return-from version-difference nil))
    (let ((diffs nil))
      (unless (equal (context-version-dimensions ctx1)
                     (context-version-dimensions ctx2))
        (push (list :dimensions
                    :old (context-version-dimensions ctx1)
                    :new (context-version-dimensions ctx2))
              diffs))
      diffs)))

;;; ============================================================
;;; Example Usage (commented out)
;;; ============================================================

#|
;; Define initial context
(defparameter *ctx1*
  (defcontext 'K_COCINA_VERDURAS
    :dimensions '(D_PARTE_COMESTIBLE)
    :universe '(C_LECHUGA C_ESPINACA C_ZANAHORIA C_APIO)))

;; Update to version 2 (add dimension)
(defparameter *ctx2*
  (update-context-version 'K_COCINA_VERDURAS
    :add-dimensions '(D_TEXTURA)
    :add-values '((D_TEXTURA . (crujiente suave)))))

;; Get current version
(get-current-version 'K_COCINA_VERDURAS)
;; => 2

;; List all versions
(context-versions 'K_COCINA_VERDURAS)
;; => list of 2 versions with changes

;; Rollback to version 1
(rollback-context 'K_COCINA_VERDURAS 1)
|#

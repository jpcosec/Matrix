;;;; tractatus-discrimination.lisp
;;;; Contextual discrimination trees, matrices, and bit dictionaries.

(defpackage #:tractatus-discrimination
  (:use #:cl))
(in-package #:tractatus-discrimination)

(defparameter *welt-dimensions* (make-hash-table :test 'eq))
(defparameter *welt-contexts* (make-hash-table :test 'eq))
(defparameter *welt-projections* (make-hash-table :test 'eq))

(defun ensure-dimension-store (welt)
  (or (gethash welt *welt-dimensions*)
      (setf (gethash welt *welt-dimensions*)
            (make-hash-table :test 'equal))))

(defun ensure-context-store (welt)
  (or (gethash welt *welt-contexts*)
      (setf (gethash welt *welt-contexts*)
            (make-hash-table :test 'equal))))

(defun ensure-projection-store (welt)
  (or (gethash welt *welt-projections*)
      (setf (gethash welt *welt-projections*)
            (make-hash-table :test 'equal))))

(defun define-dimension (welt dimension-id values &key question (type :categorical-one-hot))
  (setf (gethash dimension-id (ensure-dimension-store welt))
        (list :id dimension-id
              :question question
              :type type
              :values (copy-list values)))
  dimension-id)

(defun find-dimension (welt dimension-id)
  (or (gethash dimension-id (ensure-dimension-store welt))
      (error "Unknown dimension ~A in world ~A"
             dimension-id
             (tractatus-core::hash-id welt))))

(defun define-context (welt context-id universe task tree)
  (setf (gethash context-id (ensure-context-store welt))
        (list :id context-id
              :universe (copy-list universe)
              :task task
              :tree tree))
  context-id)

(defun find-context (welt context-id)
  (or (gethash context-id (ensure-context-store welt))
      (error "Unknown context ~A in world ~A"
             context-id
             (tractatus-core::hash-id welt))))

(defun context-universe (welt context-id)
  (copy-list (getf (find-context welt context-id) :universe)))

(defun ensure-context-projections (welt context-id)
  (let* ((store (ensure-projection-store welt))
         (context-store (gethash context-id store)))
    (or context-store
        (setf (gethash context-id store)
              (make-hash-table :test 'equal)))))

(defun ensure-concept-projection (welt context-id concept-id)
  (let* ((context-store (ensure-context-projections welt context-id))
         (concept-store (gethash concept-id context-store)))
    (or concept-store
        (setf (gethash concept-id context-store)
              (make-hash-table :test 'equal)))))

(defun project-concept (welt context-id concept-id dimension-id value)
  (let ((dimension (find-dimension welt dimension-id))
        (context (find-context welt context-id)))
    (unless (member concept-id (getf context :universe) :test #'equal)
      (error "Concept ~A does not belong to context ~A" concept-id context-id))
    (unless (member value (getf dimension :values) :test #'equal)
      (error "Invalid value ~A for dimension ~A" value dimension-id))
    (setf (gethash dimension-id (ensure-concept-projection welt context-id concept-id))
          value)
    concept-id))

(defun projected-value (welt context-id concept-id dimension-id)
  (let* ((context-store (ensure-context-projections welt context-id))
         (concept-store (gethash concept-id context-store)))
    (when concept-store
      (gethash dimension-id concept-store))))

(defun row-vector (welt context-id concept-id dimension-id)
  (let* ((dimension (find-dimension welt dimension-id))
         (values (getf dimension :values))
         (projected (projected-value welt context-id concept-id dimension-id)))
    (unless projected
      (error "Concept ~A is unassigned for dimension ~A in context ~A"
             concept-id dimension-id context-id))
    (mapcar (lambda (candidate)
              (if (equal candidate projected) 1 0))
            values)))

(defun build-matrix (welt context-id dimension-id)
  (let* ((context (find-context welt context-id))
         (dimension (find-dimension welt dimension-id))
         (universe (getf context :universe))
         (values (getf dimension :values)))
    (list :context context-id
          :dimension dimension-id
          :row-axis (copy-list universe)
          :col-axis (copy-list values)
          :values (mapcar (lambda (concept-id)
                            (list concept-id (row-vector welt context-id concept-id dimension-id)))
                          universe))))

(defun transpose-index (matrix)
  (let* ((values (getf matrix :col-axis))
         (rows (getf matrix :values))
         (index (make-hash-table :test 'equal)))
    (dolist (value values)
      (setf (gethash value index) '()))
    (dolist (row rows)
      (destructuring-bind (concept-id vector) row
        (loop for value in values
              for bit in vector do
          (when (= bit 1)
            (push concept-id (gethash value index))))))
    (let ((result '()))
      (dolist (value values)
        (push (list value (nreverse (gethash value index))) result))
      (nreverse result))))

(defun detect-collisions (transposed-index)
  (remove nil
          (mapcar (lambda (entry)
                    (destructuring-bind (value bucket) entry
                      (when (> (length bucket) 1)
                        (list :value value :concepts bucket :status :unresolved))))
                  transposed-index)))

(defun tree-node-branches (node)
  (getf node :branches))

(defun tree-node-dimension (node)
  (getf node :dimension))

(defun tree-branch-child (branch)
  (getf (rest branch) :next))

(defun path-token (dimension value)
  (format nil "~A.~A" dimension value))

(defun flatten-tree-paths (node &optional conditions)
  (let ((dimension (tree-node-dimension node))
        (result '()))
    (dolist (branch (tree-node-branches node))
      (let* ((value (first branch))
             (child (tree-branch-child branch))
             (entry (list :path (append conditions (list (list dimension value)))
                          :dimension dimension
                          :value value
                          :token (path-token dimension value))))
        (push entry result)
        (when child
          (setf result (nconc (nreverse (flatten-tree-paths child
                                                             (append conditions (list (list dimension value)))))
                              result)))))
    (nreverse result)))

(defun bit-dictionary (welt context-id)
  (let* ((context (find-context welt context-id))
         (tree (getf context :tree))
         (paths (flatten-tree-paths tree))
         (result '()))
    (dolist (entry paths)
      (push (list :bit nil
                  :path (copy-tree (getf entry :path))
                  :token-path (mapcar (lambda (step)
                                        (path-token (first step) (second step)))
                                      (getf entry :path))
                  :dimension (getf entry :dimension)
                  :value (getf entry :value))
            result))
    (setf result (stable-sort (nreverse result)
                              #'<
                              :key (lambda (entry)
                                     (length (getf entry :path)))))
    (loop for entry in result
          for index from 0 do
      (setf (getf entry :bit) index))
    result))

(defun path-prefix-matches-p (welt context-id concept-id path &key include-last)
  (let ((steps (if include-last path (butlast path))))
    (every (lambda (step)
             (equal (projected-value welt context-id concept-id (first step))
                    (second step)))
           steps)))

(defun concept-signature (welt context-id concept-id)
  (let ((buffer (make-string-output-stream)))
    (dolist (entry (bit-dictionary welt context-id))
      (let ((path (getf entry :path)))
        (write-char (if (path-prefix-matches-p welt context-id concept-id path :include-last t)
                        #\1
                        #\0)
                    buffer)))
    (get-output-stream-string buffer)))

(defun concept-valid-mask (welt context-id concept-id)
  (let ((buffer (make-string-output-stream)))
    (dolist (entry (bit-dictionary welt context-id))
      (let ((path (getf entry :path)))
        (write-char (if (path-prefix-matches-p welt context-id concept-id path :include-last nil)
                        #\1
                        #\0)
                    buffer)))
    (get-output-stream-string buffer)))

(defun neighbors (welt context-id concept-id dimension-id)
  (let* ((matrix (build-matrix welt context-id dimension-id))
         (buckets (transpose-index matrix))
         (value (projected-value welt context-id concept-id dimension-id))
         (same (copy-list (second (assoc value buckets :test #'equal))))
         (contrasts '()))
    (dolist (entry buckets)
      (unless (equal (first entry) value)
        (setf contrasts (append contrasts (copy-list (second entry))))))
    (list :similar (remove concept-id same :test #'equal)
          :contrastive contrasts)))

;;;; tractatus-worlds.lisp
;;;; World naming, creation, and placement rules.

(defpackage #:tractatus-worlds
  (:use #:cl))
(in-package #:tractatus-worlds)

(defparameter *allowed-ingestion-kinds* '(:repo :doc :section :hyp :session :branch :lang :lex))

(defun ascii-alphanumeric-p (char)
  (or (alpha-char-p char) (digit-char-p char)))

(defun split-string-on-char (string delimiter)
  (let ((parts '())
        (start 0)
        (length (length string)))
    (labels ((emit-part (end)
               (push (subseq string start end) parts)))
      (loop for index from 0 below length do
        (when (char= (char string index) delimiter)
          (emit-part index)
          (setf start (1+ index))))
      (emit-part length))
    (nreverse parts)))

(defun normalize-welt-segment (value)
  (let* ((raw (string-downcase (string value)))
         (buffer (make-string-output-stream))
         (pending-hyphen nil))
    (loop for char across raw do
      (cond
        ((ascii-alphanumeric-p char)
         (when pending-hyphen
           (write-char #\- buffer)
           (setf pending-hyphen nil))
         (write-char char buffer))
        ((member char '(#\Space #\Tab #\/ #\_ #\. #\: #\\ #\#) :test #'char=)
         (setf pending-hyphen t))
        (t
         (setf pending-hyphen t))))
    (let ((normalized (get-output-stream-string buffer)))
      (if (string= normalized "")
          "unnamed"
          normalized))))

(defun normalize-repo-name (repo)
  (normalize-welt-segment repo))

(defun normalize-branch-name (branch)
  (normalize-welt-segment branch))

(defun normalize-path-components (path)
  (remove-if (lambda (segment) (string= segment ""))
             (mapcar #'normalize-welt-segment
                     (split-string-on-char path #\/))))

(defun join-with-slash (segments)
  (format nil "~{~A~^/~}" segments))

(defun make-lang-welt-id (language)
  (join-with-slash (list "lang" (normalize-welt-segment language))))

(defun make-lex-welt-id (repo topic)
  (join-with-slash (list "lex"
                         (normalize-repo-name repo)
                         (normalize-welt-segment topic))))

(defun make-repo-welt-id (repo)
  (join-with-slash (list "repo" (normalize-repo-name repo))))

(defun make-branch-welt-id (repo branch)
  (join-with-slash (list "branch"
                         (normalize-repo-name repo)
                         (normalize-branch-name branch))))

(defun make-doc-welt-id (repo path)
  (join-with-slash (append (list "doc" (normalize-repo-name repo))
                           (normalize-path-components path))))

(defun make-section-welt-id (repo path section)
  (join-with-slash (append (list "section" (normalize-repo-name repo))
                           (normalize-path-components path)
                           (list (normalize-welt-segment section)))))

(defun make-hyp-welt-id (repo topic)
  (join-with-slash (list "hyp"
                         (normalize-repo-name repo)
                         (normalize-welt-segment topic))))

(defun welt-kind-from-id (welt-id)
  (let ((parts (split-string-on-char welt-id #\/)))
    (and parts (intern (string-upcase (first parts)) :keyword))))

(defun infer-parent-welt-id (welt-id)
  (let ((parts (split-string-on-char welt-id #\/)))
    (cond
      ((or (null parts) (< (length parts) 2)) nil)
      ((string= (first parts) "section")
       (join-with-slash (cons "doc" (rest (butlast parts)))))
      ((or (string= (first parts) "doc")
           (string= (first parts) "branch"))
       (join-with-slash (list "repo" (second parts))))
      (t nil))))

(defun make-welt (&key id)
  (make-instance 'tractatus-core::welt :hash-id id))

(defun direct-ingestion-allowed-p (welt)
  (member (welt-kind-from-id (tractatus-core::hash-id welt))
          *allowed-ingestion-kinds*))

(defun assert-ingestion-target (welt)
  (unless (direct-ingestion-allowed-p welt)
    (error "Direct ingestion into world ~A is not allowed by policy."
           (tractatus-core::hash-id welt)))
  welt)

(defun make-doc-welt (repo path)
  (make-welt :id (make-doc-welt-id repo path)))

(defun make-section-welt (repo path section)
  (make-welt :id (make-section-welt-id repo path section)))

(defun make-repo-welt (repo)
  (make-welt :id (make-repo-welt-id repo)))

(defun make-branch-welt (repo branch)
  (make-welt :id (make-branch-welt-id repo branch)))

(defun make-lang-welt (language)
  (make-welt :id (make-lang-welt-id language)))

(defun make-lex-welt (repo topic)
  (make-welt :id (make-lex-welt-id repo topic)))

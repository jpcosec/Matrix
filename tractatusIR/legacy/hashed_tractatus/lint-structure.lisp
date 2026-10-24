;;;; lint-structure.lisp
;;;; Architectural lint for the WeltGraph Lisp layout.

(defparameter *core-file* "tractatus-core.lisp")
(defparameter *periphery-file* "tractatus-periphery.lisp")
(defparameter *ring-file* "tractatus-ring.lisp")
(defparameter *worlds-file* "tractatus-worlds.lisp")
(defparameter *semantics-file* "tractatus-semantics.lisp")

(defparameter *core-forbidden-substrings*
  '("defparameter"
    "defvar"
    "with-open-file"
    "open "
    "uiop:run-program"
    "run-program"
    "socket"
    "http"
    "json"
    "tractatus-ring"
    "tractatus-worlds"
    "tractatus-semantics"))

(defun read-file-as-string (path)
  (with-open-file (stream path :direction :input)
    (let ((buffer (make-string (file-length stream))))
      (read-sequence buffer stream)
      buffer)))

(defun contains-substring-p (substring string)
  (not (null (search substring string :test #'char-equal))))

(defun assert-no-forbidden-substrings (path substrings)
  (let ((content (read-file-as-string path)))
    (dolist (substring substrings)
      (when (contains-substring-p substring content)
        (error "Architectural lint failed: ~A contains forbidden substring ~S"
               path substring)))))

(defun assert-no-core-backreferences ()
  (let ((content (read-file-as-string *core-file*)))
    (when (contains-substring-p "tractatus-periphery" content)
      (error "Architectural lint failed: core must not depend on periphery"))))

(defun assert-ring-does-not-point-back-to-core-file-role ()
  (let ((content (read-file-as-string *ring-file*)))
    (when (contains-substring-p "(load \"tractatus-core.lisp\")" content)
      (error "Architectural lint failed: ring must not manage load-order internally"))))

(defun run-lint ()
  (assert-no-forbidden-substrings *core-file* *core-forbidden-substrings*)
  (assert-no-core-backreferences)
  (assert-ring-does-not-point-back-to-core-file-role)
  (format t "Structural lint passed.~%"))

(run-lint)

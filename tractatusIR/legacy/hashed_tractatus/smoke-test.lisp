(load "tractatus-core.lisp")
(load "tractatus-periphery.lisp")

(in-package #:tractatus-core)

(defun expect (condition message)
  (unless condition
    (error "Test failed: ~A" message)))

(let* ((world (make-instance 'welt :hash-id "w-test"))
       (rules (make-hash-table :test 'equal))
       (valid-rule
         (make-instance 'logische-regel
                        :hash-id "r-has-color"
                        :struktur :has-color
                        :validador (lambda (objects welt)
                                     (and (= (length objects) 2)
                                          (instance-of-p (first objects) 'physical-object welt)
                                          (instance-of-p (second objects) 'color welt))))))
  (register-begriff world 'entity)
  (register-begriff world 'physical-object :subclase-de 'entity)
  (register-begriff world 'vehicle :subclase-de 'physical-object)
  (register-begriff world 'color :subclase-de 'entity)
  (register-gegenstand world 'my-car :instancia-de 'vehicle)
  (register-gegenstand world 'red :instancia-de 'color)
  (register-gegenstand world 'idea :instancia-de 'entity)
  (setf (gethash :has-color rules) valid-rule)
  (let ((sv (make-instance 'sachverhalt
                           :hash-id "sv-1"
                           :objekte '(my-car red)
                           :struktur :has-color)))
    (assert-tatsache sv world rules)
    (expect (truth-of sv world) "asserted fact should be true in world"))
  (handler-case
      (progn
        (assert-tatsache (make-instance 'sachverhalt
                                        :hash-id "sv-2"
                                        :objekte '(idea red)
                                        :struktur :has-color)
                         world
                         rules)
        (error "Expected syntax violation"))
    (sinsentido-error () t))
  (format t "Smoke test passed.~%"))

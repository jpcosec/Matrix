(load "tractatus-core.lisp")
(load "tractatus-periphery.lisp")
(load "tractatus-worlds.lisp")
(load "tractatus-ring.lisp")

(in-package #:tractatus-ring)

(defun expect (condition message)
  (unless condition
    (error "Test failed: ~A" message)))

(let* ((world (tractatus-worlds::make-doc-welt "hum-ecosystem" "graphlang/ring-smoke-test.md"))
       (rules (make-hash-table :test 'equal))
       (valid-rule
         (make-instance 'tractatus-core::logische-regel
                        :hash-id "r-has-color"
                        :struktur :has-color
                        :validador (lambda (objects welt)
                                     (and (= (length objects) 2)
                                          (tractatus-core::instance-of-p (first objects) 'vehicle welt)
                                          (tractatus-core::instance-of-p (second objects) 'color welt))))))
  (tractatus-core::register-begriff world 'entity)
  (tractatus-core::register-begriff world 'vehicle :subclase-de 'entity)
  (tractatus-core::register-begriff world 'color :subclase-de 'entity)
  (tractatus-core::register-gegenstand world "car-1" :instancia-de 'vehicle)
  (tractatus-core::register-gegenstand world "color-red" :instancia-de 'color)
  (register-sign-binding "auto" "car-1" world)
  (register-sign-binding "rojo" "color-red" world)
  (setf (gethash :has-color rules) valid-rule)
  (process-sldb-document '(:fields ("El auto es rojo")) world rules)
  (let ((unknown-a (resolve-name "verde" world))
        (unknown-b (resolve-name "motor" world)))
    (expect (not (string= unknown-a unknown-b))
            "different unknown signs should get different ids")
    (expect (string= unknown-a (resolve-name "verde" world))
            "the same sign should resolve consistently inside one world"))
  (let ((sv (make-instance 'tractatus-core::sachverhalt
                           :objekte '("car-1" "color-red")
                           :struktur :has-color)))
    (expect (tractatus-core::truth-of sv world)
            "document ingestion should assert a true fact"))
  (format t "Ring smoke test passed.~%"))

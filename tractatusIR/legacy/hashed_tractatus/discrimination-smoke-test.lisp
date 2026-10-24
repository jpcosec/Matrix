(load "tractatus-core.lisp")
(load "tractatus-periphery.lisp")
(load "tractatus-worlds.lisp")
(load "tractatus-discrimination.lisp")

(in-package #:cl)

(defun expect (condition message)
  (unless condition
    (error "Test failed: ~A" message)))

(let ((world (tractatus-worlds::make-lex-welt "hum-ecosystem" "cocina")))
  (tractatus-discrimination::define-dimension world :parte-comestible '(hoja raiz tallo)
                                              :question "Que parte se consume?")
  (tractatus-discrimination::define-dimension world :estructura-hoja '(cabeza-compacta hoja-suelta)
                                              :question "Como se organiza la hoja?")
  (tractatus-discrimination::define-dimension world :grosor-hoja '(delgada gruesa)
                                              :question "Que grosor tiene la hoja?")
  (tractatus-discrimination::define-context
   world
   :k-cocina-verduras
   '(lechuga zanahoria apio espinaca acelga)
   :diferenciar
   '(:dimension :parte-comestible
     :branches ((hoja :next (:dimension :estructura-hoja
                              :branches ((cabeza-compacta)
                                         (hoja-suelta :next (:dimension :grosor-hoja
                                                              :branches ((delgada)
                                                                         (gruesa)))))))
                (raiz)
                (tallo))))
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'lechuga :parte-comestible 'hoja)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'lechuga :estructura-hoja 'cabeza-compacta)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'zanahoria :parte-comestible 'raiz)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'apio :parte-comestible 'tallo)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'espinaca :parte-comestible 'hoja)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'espinaca :estructura-hoja 'hoja-suelta)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'espinaca :grosor-hoja 'delgada)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'acelga :parte-comestible 'hoja)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'acelga :estructura-hoja 'hoja-suelta)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'acelga :grosor-hoja 'gruesa)
  (let ((rejected nil))
    (handler-case
        (tractatus-discrimination::project-concept world :k-cocina-verduras 'martillo :parte-comestible 'tallo)
      (error () (setf rejected t)))
    (expect rejected "concepts outside the local universe should be rejected"))
  (tractatus-discrimination::define-context world :k-incomplete '(lechuga zanahoria) :diferenciar
                                            '(:dimension :parte-comestible
                                              :branches ((hoja) (raiz) (tallo))))
  (tractatus-discrimination::project-concept world :k-incomplete 'lechuga :parte-comestible 'hoja)
  (let ((failed nil))
    (handler-case
        (tractatus-discrimination::build-matrix world :k-incomplete :parte-comestible)
      (error () (setf failed t)))
    (expect failed "missing discriminant values should fail fast during matrix build"))
  (let* ((matrix (tractatus-discrimination::build-matrix world :k-cocina-verduras :parte-comestible))
         (index (tractatus-discrimination::transpose-index matrix))
         (collisions (tractatus-discrimination::detect-collisions index))
         (dictionary (tractatus-discrimination::bit-dictionary world :k-cocina-verduras))
         (spinach-signature (tractatus-discrimination::concept-signature world :k-cocina-verduras 'espinaca))
         (carrot-validity (tractatus-discrimination::concept-valid-mask world :k-cocina-verduras 'zanahoria))
         (neighbors (tractatus-discrimination::neighbors world :k-cocina-verduras 'lechuga :parte-comestible)))
    (expect (equal (getf matrix :col-axis) '(hoja raiz tallo))
            "top-level discriminant matrix should preserve declared values")
    (expect (equal (second (assoc 'hoja index :test #'equal)) '(lechuga espinaca acelga))
            "transpose index should bucket same-value concepts together")
    (expect (= (length collisions) 1)
            "top-level leaf bucket should collide")
    (expect (= (length dictionary) 7)
            "bit dictionary should encode all discriminant tree branches")
    (expect (string= spinach-signature "1000110")
            "spinach should activate the expected discriminative path")
    (expect (string= carrot-validity "1110000")
            "carrot should mask out non-applicable leaf dimensions")
    (expect (equal (getf neighbors :similar) '(espinaca acelga))
            "neighbors should derive horizontal similarity from shared bucket"))
  (format t "Discrimination smoke test passed.~%"))

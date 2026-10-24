(load "tractatus-core.lisp")
(load "tractatus-periphery.lisp")
(load "tractatus-worlds.lisp")
(load "tractatus-discrimination.lisp")
(load "tractatus-discrimination-persistence.lisp")

(in-package #:cl)

(defun expect (condition message)
  (unless condition
    (error "Test failed: ~A" message)))

(let* ((world (tractatus-worlds::make-lex-welt "hum-ecosystem" "cocina"))
       (loaded (tractatus-worlds::make-lex-welt "hum-ecosystem" "cocina"))
       (output #P"./tmp-snapshots/discrimination/"))
  (tractatus-discrimination::define-dimension world :parte-comestible '(hoja raiz tallo))
  (tractatus-discrimination::define-dimension world :estructura-hoja '(cabeza-compacta hoja-suelta))
  (tractatus-discrimination::define-context
   world
   :k-cocina-verduras
   '(lechuga zanahoria espinaca)
   :diferenciar
   '(:dimension :parte-comestible
     :branches ((hoja :next (:dimension :estructura-hoja
                              :branches ((cabeza-compacta)
                                         (hoja-suelta))))
                (raiz)
                (tallo))))
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'lechuga :parte-comestible 'hoja)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'lechuga :estructura-hoja 'cabeza-compacta)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'zanahoria :parte-comestible 'raiz)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'espinaca :parte-comestible 'hoja)
  (tractatus-discrimination::project-concept world :k-cocina-verduras 'espinaca :estructura-hoja 'hoja-suelta)
  (tractatus-discrimination-persistence::save-discrimination-state world output)
  (tractatus-discrimination-persistence::load-discrimination-state
   loaded
   (merge-pathnames "discrimination.sexp" output))
  (expect (equal (getf (tractatus-discrimination::build-matrix loaded :k-cocina-verduras :parte-comestible) :col-axis)
                 '(hoja raiz tallo))
          "loaded discrimination state should preserve dimension ordering")
  (expect (string= (tractatus-discrimination::concept-signature loaded :k-cocina-verduras 'espinaca)
                   "10001")
          "loaded discrimination state should preserve path signatures")
  (format t "Discrimination persistence smoke test passed.~%"))

;;;; tractatus.asd
;;;; ASDF system definition for Tractatus Lisp implementation

(defsystem :tractatus
  :name "tractatus"
  :description "Lisp implementation of Tractarian semantic disambiguation system"
  :version "0.1"
  :author "GraphLang Project"
  :license "MIT"
  :depends-on (:split-sequence)
  :components
  ((:module "datype+operations"
     :pathname "datype+operations"
     :components ((:file "tractatus-signatures")))
   (:module "sin-mask+tractatus-logic"
     :pathname "sin-mask+tractatus logic"
     :depends-on ("datype+operations")
     :components ((:file "tractatus-semantics")))
   (:module "higher-functions"
     :pathname "higher functions"
     :depends-on ("datype+operations" "sin-mask+tractatus-logic")
     :components
     ((:file "tractatus-discrimination")
      (:file "tractatus-update" :depends-on ("tractatus-discrimination"))
      (:file "tractatus-selection" :depends-on ("tractatus-discrimination"))
      (:file "tractatus-security")
      (:file "tractatus-inference")
      (:file "tractatus-versioning")))
   (:module "encoding"
     :pathname "encoding"
     :depends-on ("higher-functions")
     :components
     ((:file "tractatus-parser")
      (:file "tractatus-nl2projection" :depends-on ("tractatus-parser"))))
   (:module "decoding"
     :pathname "decoding"
     :depends-on ("encoding")
     :components ())
   (:module "utils"
     :pathname "utils"
     :depends-on ("higher-functions" "encoding")
     :components
     ((:file "tractatus-db")
      (:file "demo")))))

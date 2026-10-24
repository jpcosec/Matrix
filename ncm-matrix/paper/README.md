# Borrador Matrix–NCM

Documento en español, versión 0.1, 23 de octubre de 2026.

- `main.tex`: fuente editable.
- `references.bib`: bibliografía externa y referencia interna explícita a Matrix.
- `main.pdf`: versión compilada.

Compilar desde este directorio con TeX Live (pdfLaTeX y BibTeX):

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

El texto distingue fundamentos de Matrix, propuesta matemática, implementación
existente y resultados medidos. Los números vienen de `../artifacts/report.json`;
no se ejecutó un entrenamiento nuevo para redactarlo. La arquitectura completa
y el protocolo WebNLG son propuestas pendientes, no resultados experimentales.

Antes de una presentación formal: completar autoría y afiliación; revisar las
definiciones propuestas de campo/ruteo; fijar una instantánea reproducible del
árbol Matrix; ampliar comparación bibliográfica; ejecutar ablaciones y varias
semillas. La referencia interna de Matrix no se presenta como publicación.

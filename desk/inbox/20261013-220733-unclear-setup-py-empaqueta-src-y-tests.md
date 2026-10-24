---
kind: unclear
sender_project: Matrix
created_at: 2026-10-13T22:07:33
status: open
---

# `setup.py` empaqueta `src` y `tests`, no los módulos reales

`pip install -e .` "funciona", pero instala el paquete equivocado: el import name
`matrix_engine` no existe y los módulos reales quedan inalcanzables.

## Evidencia

- `setup.py` usa `packages=find_packages()` sin `package_dir`.
- `src/__init__.py` existe, así que `find_packages()` descubre `src` (y `tests`) como paquetes de primer nivel.
- `matrix_engine.egg-info/top_level.txt` contiene `src` y `tests`.
- El editable finder mapea `src`, `tests`, `tools` — no los módulos reales.
- Resultado: `import matrix_engine` → `ModuleNotFoundError`; los paquetes reales
  (`external_formats`, `operational_model`) viven bajo `src/` y tampoco resuelven al importarlos.

## Origen

Defecto del propio repo (preexistente). No lo introdujo la reorganización del
workspace: el editable quedó apuntando a la ruta correcta
(`wittgenstein/Matrix/Matrix/src`), el problema es la declaración de paquetes.

## Fix propuesto

Alinear el layout `src/`:

```python
setup(
    ...
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    ...
)
```

Alternativa mínima: eliminar `src/__init__.py` (no es un paquete, es el directorio raíz del layout).

Reinstalar tras el cambio: `pip install -e wittgenstein/Matrix/Matrix --no-deps`.

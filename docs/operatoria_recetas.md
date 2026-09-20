# Operatoria: cómo leer una receta

Spec autorada (no extraída) que define cómo se lee una receta como **máquina de
estados**. Es la capa de infraestructura: sin ella, el texto sólo da pasos
sueltos; con ella, da transiciones, guardas y validez.

- Spec: `tools/kb/operatoria/recetas.yaml` y `tools/kb/operatoria/fsm.yaml`
- Se materializa como un contexto más: `ctx:operatoria` → `wigame:operatoria:declara`
- `compile` la consulta para decidir qué cierres aplica y qué validaciones corre
- Registro conceptual: átomo `Aplicaciones/Dominio_Culinario/Operatoria_Lectura_de_Recetas.md`

## Reglas de lectura (texto → proposiciones)

| marca en el texto | proposición | ejemplo |
|---|---|---|
| orden explícito ("luego", "una vez que", "a continuación") | `(precede A B)` | `precede picar sofreir` |
| precondición ("cuando el fondo está dorado", "hasta que") | `(requiere A condición)` | `requiere desglasar fondo_dorado` |
| ingrediente o herramienta | `(usa A item)` | `usa sofreir manteca` |
| resultado ("hasta obtener una salsa") | `(produce A resultado)` | `produce cocinar_lento salsa_espesa` |
| simultaneidad ("mientras", "en paralelo") | `(paralelo_con A B)` | conmutativa: el orden no importa |
| equivalencia declarada ("si no hay X, usar Y") | `(sustituye_a X Y)` | cadena transitiva |

No se extrae (todavía): cantidades exactas, tiempos, marcas, temperaturas.

## Álgebra declarada

| relación | álgebra | consecuencia operativa |
|---|---|---|
| `precede` | transitiva, asimétrica | cierre ⇒ alcanzabilidad; `A+ = A · A*` |
| `requiere` | simple | guarda: sin precondición el paso no aplica |
| `usa` | simple | pertenencia de recursos |
| `produce` | simple | efecto del paso |
| `sustituye_a` | transitiva | cadena de sustituciones |
| `paralelo_con` | conmutativa | orden indistinto |

## Operaciones admisibles

| operación | qué hace | chequeo |
|---|---|---|
| `cierre_precede` | cierra `precede` y deriva hechos | derivados verificados con `verify` |
| `orden_aciclico` | exige DAG (recetas) | ciclos ⇒ error `ciclo` |
| `alcanzable` | ¿de A se llega a B? | cierre vs oráculo BFS |
| `guarda_precondicion` | ¿el paso tiene su precondición? | precondición faltante ⇒ `unsinnig` |
| `sustitucion_transitiva` | cadena de sustitutos | `manteca → margarina` |
| `minimizar_estados` (fsm) | clases de equivalencia de estados | firma de salidas cruda |

## Dónde aparece el sentido (`Si`)

- `Si=1` (`sinnvoll`): la operación aplica en este contexto.
- `Si=0` (`unsinnig`): la operación no aplica al dominio (p. ej. exigir aciclicidad en una FSM, o un ingrediente categorialmente ajeno dentro del juego de la carne).

## Verificación medida

- `ragout`, `guiso`, `bechamel`: acíclicas, con cierre derivado (10, 10 y 6 aristas) y acuerdo total con el oráculo BFS.
- `trafico`: ciclo esperado (`rojo→verde→amarillo→rojo`), `verde_peatonal` **inalcanzable** desde `rojo` y **equivalente** a `verde` (misma firma de salidas ⇒ candidato a minimizar).
- `ascensor`: fuertemente conectada; `piso_1` y `piso_3` con la misma firma.
- Sustitución transitiva: `(sustituye_a manteca margarina)` se responde `true` sin estar escrita.
- Compartidos entre recetas (`shared`): `cebolla`, `vino`, `caldo` (guiso ↔ ragout), `manteca` (bechamel ↔ ragout).

## Límites actuales

- Guardas booleanas solamente: no hay cantidades ni rangos (no se puede decir "250 g").
- Sin noción de tiempo: `precede` es orden parcial, no duración.
- `paralelo_con` declara conmutatividad pero el compilador todavía no la explota en planificación.
- La minimización usa firma de salidas cruda; la equivalencia fuerte (misma clase de destino) queda pendiente.

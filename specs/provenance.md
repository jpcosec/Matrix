# Procedencia y resolución de conflictos

## 1. Dónde vive

En `Fact.evidence` (`matrix/src/operational_model/core/fact.py:20`, `dict[str, Any]`). Hoy no tiene esquema, solo lo escribe un test y lo serializa `system/wi_game_serialization.py:85,125`; `assert` crea `Fact` con `evidence={}`. Esta spec le da esquema. No se crean matrices de procedencia.

```json
{
  "prov": [
    {"document_id": "recetas/ragout.md", "span": [412, 468], "extractor": "populator@0.1", "confidence": 0.97}
  ],
  "tier": "statistical",
  "curation": "proposed",
  "stats": {"phi": 0.9999, "phi_entropic": 0.777, "n": 4000, "n_a": 600, "n_b": 1400, "n_anb": 200},
  "derived_from": ["fact:…", "fact:…"],
  "history": [{"at": "2026-09-18T03:10:00Z", "by": "jp", "action": "confirm", "note": "…"}]
}
```

- `prov`: lista de `Prov(f) = (document_id, span, extractor, confidence)` (átomo `Procedencia_y_Evidencia` de Matrix). Un hecho puede tener varias citas.
- `tier`: nivel epistémico (§2). `curation`: `proposed | confirmed | rejected`.
- `stats`: los números de `sia/` que justificaron la propuesta.
- `derived_from`: para hechos inferidos, las premisas (`fact_id`) usadas por `v ⊗ I*`.
- `history`: cada cambio de estado, con autor y motivo.

## 2. Niveles

| `tier` | Quién lo pone | `truth` típica | Precedencia |
|---|---|---|---|
| `observed` | humano o telemetría, directamente (`assert`) | `TRUE`/`FALSE` | 1 (máxima) |
| `confirmed` | propuesto por `sia/`+LLM, confirmado por humano (`promote`) | `TRUE` | 2 |
| `inferred` | modus ponens sobre `I*` | `TRUE` | 3 |
| `statistical` | `sia/report` sin curar | `UNKNOWN` | 4 |

Un hecho `statistical` nunca participa en la deducción: `UNKNOWN` no activa filas de `I`. Solo `confirmed` y `observed` alimentan `v`.

## 3. Conflictos

Política tomada del átomo `Manejo_de_Contradicciones` de Matrix: un candidato que contradice `V_i` emite una **señal explícita** (`OperationResult.status="reject", sinn="widerspruechlich"`, ya implementado en `system/s_expression_runtime.py:129`); nunca se sobrescribe en silencio. Tres resoluciones:

1. **One-hot estricto:** si la relación es exclusiva (p. ej. `color`), afirmar un segundo valor se rechaza por invariante.
2. **Objeto de contradicción:** el conflicto se registra como estado inestable y se pide una dimensión discriminativa `D_i` (p. ej. "¿en qué contexto?"), que abre un `WiGame` hijo.
3. **Por confianza:** entre niveles gana el `tier` de mayor precedencia; dentro del mismo nivel gana el `confidence` mayor y, a igualdad, el más reciente; el perdedor pasa a `history`, no se borra.

`retract` (nuevo verbo) no destruye: pone `truth=FALSE` o `UNKNOWN` según se indique y anota `history`.

## 4. Qué se implementa

- Esquema anterior como `TypedDict` en `matrix/src/operational_model/core/evidence.py` + validación en `add_fact`.
- `assert` acepta `evidence` opcional; `promote` lo rellena desde el candidato.
- `why` recorre `derived_from` y `prov`.

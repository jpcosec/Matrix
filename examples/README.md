# Examples

WiGame serializations in the new operational model format.

## Files

| File | Description |
|------|-------------|
| `vegetales.yaml` | Single WiGame: vegetables with leaf/root/stem properties |
| `colores.yaml` | Single WiGame: colors |
| `multivalued.yaml` | Single WiGame with true/false/∅/unsinnig truth values |
| `vegetales_hierarchical.yaml` | Top-level WiGame (vegetables) |
| `hojas_sub.yaml` | Sub-WiGame (leaf details), linked via context_id |
| `unified_vegetales.yaml` | Same data, separate WiGame for cross-linking demo |
| `unified_colores.yaml` | Color WiGame for cross-linking demo |

## s-expression form

Every fact in these WiGames is equivalent to `(R subj term)`.

```
(R has_property lechuga hoja)
(R has_property lechuga hoja.lisa)
...
```

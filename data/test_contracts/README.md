# Contratos de prueba

Cuatro imágenes PNG (documentos **ficticios**) que forman dos pares *contrato original → adenda*.
Se generan con `python scripts/generate_test_contracts.py` y también se puede usar cualquier otro par
de imágenes JPEG/PNG (por ejemplo los de la carpeta de recursos del curso).

| Par | Archivos | Escenario | Complejidad |
|---|---|---|---|
| 1 | `par1_original.png` + `par1_adenda.png` | Contrato de prestación de servicios | **Simple**: 2 cambios |
| 2 | `par2_original.png` + `par2_adenda.png` | Acuerdo de confidencialidad | **Compleja**: 3 cambios de 3 tipos distintos |

## Resultado esperado (ground truth)

### Par 1 — cambios simples
| Tipo | Sección | Cambio |
|---|---|---|
| MODIFICACIÓN | Cláusula TERCERA (Precio y forma de pago) | Monto mensual: USD 2.500 → USD 2.850 |
| MODIFICACIÓN | Cláusula SEGUNDA (Vigencia y vencimiento) | Vencimiento: 28/02/2026 → 31/08/2026 |

Temas esperados: Precio, Plazo y vigencia.

### Par 2 — cambios complejos
| Tipo | Sección | Cambio |
|---|---|---|
| MODIFICACIÓN | Cláusula TERCERA (Alcance territorial) | Solo Argentina → Argentina, Uruguay y Chile |
| ELIMINACIÓN | Cláusula CUARTA inciso b) (Restricciones de uso) | Se elimina la prohibición de hacer copias |
| ADICIÓN | Cláusula OCTAVA (nueva) | Protección de datos personales (Ley 25.326, aviso de incidentes en 72 h) |

Temas esperados: Alcance territorial, Restricciones de uso, Protección de datos / Confidencialidad.

> Nota para evaluar el sistema: los incisos a) y c) de la cláusula CUARTA y las cláusulas no mencionadas
> **no** cambian. Un buen resultado no debe reportarlos como modificados.

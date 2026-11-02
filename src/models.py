"""Modelos Pydantic del sistema.

`ContractChangeOutput` es el contrato de salida del pipeline: exactamente tres
campos, con tipos y descripciones. Se usa con `model_validate()` para garantizar
que lo que sale del Agente 2 es estructuralmente correcto antes de entregarlo
a los sistemas de LegalMove.
"""

from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContractChangeOutput(BaseModel):
    """Resultado estructurado de la comparación entre un contrato y su adenda."""

    # extra="forbid": si el modelo agrega una clave que no pedimos, la validación falla.
    # str_strip_whitespace: limpia espacios sobrantes en todos los strings.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    sections_changed: List[str] = Field(
        description=(
            "Identificadores de las secciones del contrato que la adenda modifica, agrega o elimina. "
            "Ej: ['Cláusula 3 - Precio', 'Cláusula 5 - Vigencia']."
        ),
    )
    topics_touched: List[str] = Field(
        description=(
            "Categorías legales o comerciales afectadas por los cambios. "
            "Ej: ['Precio', 'Plazo y vigencia', 'Confidencialidad']."
        ),
    )
    summary_of_the_change: str = Field(
        min_length=1,
        description=(
            "Descripción detallada de cada cambio, indicando si es una ADICIÓN, ELIMINACIÓN o MODIFICACIÓN "
            "y, cuando corresponda, el valor anterior y el nuevo."
        ),
    )

    @field_validator("sections_changed", "topics_touched")
    @classmethod
    def _no_blank_items(cls, items: List[str]) -> List[str]:
        """Rechaza elementos vacíos y elimina duplicados conservando el orden."""
        cleaned: List[str] = []
        for item in items:
            item = item.strip()
            if not item:
                raise ValueError("la lista no puede contener elementos vacíos")
            if item not in cleaned:
                cleaned.append(item)
        return cleaned

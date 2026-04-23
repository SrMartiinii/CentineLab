"""
Schemas Pydantic — Resultado
Al crear un resultado, el endpoint llama al motor de alertas automáticamente.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ResultadoCreate(BaseModel):
    """
    Datos para registrar el valor de un parámetro analítico.
    El campo 'parametro' debe coincidir con las claves de CLINICAL_RANGES
    para que el motor de alertas pueda evaluarlo correctamente.
    """

    parametro:  str       # Ej: "potasio", "glucosa", "troponina_i"
    valor:      float     # Valor numérico del analizador
    unidad:     str       # Ej: "mEq/L", "mg/dL", "ng/mL"
    muestra_id: int
    fuente:     Optional[str] = None  # Nombre del analizador o laboratorio

    @field_validator("parametro")
    @classmethod
    def normalizar_parametro(cls, v: str) -> str:
        """Normaliza el nombre del parámetro: minúsculas y sin espacios extra."""
        return v.strip().lower()

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v: float) -> float:
        """Los valores analíticos no pueden ser negativos."""
        if v < 0:
            raise ValueError("El valor analítico no puede ser negativo.")
        return v


class ResultadoOut(BaseModel):
    id:         int
    parametro:  str
    valor:      float
    unidad:     str
    muestra_id: int
    fuente:     Optional[str]
    created_at: datetime

    # Incluye la alerta si se generó, None si el valor es normal
    alerta:     Optional["AlertaOut"] = None

    model_config = {"from_attributes": True}


# Importación tardía para evitar importación circular (Alerta → Resultado → Alerta)
from app.schemas.alerta import AlertaOut  # noqa: E402
ResultadoOut.model_rebuild()

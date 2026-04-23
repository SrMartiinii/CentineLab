"""
Schemas Pydantic — Alerta
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.alerta import SeveridadAlerta


class AlertaOut(BaseModel):
    """
    Datos de una alerta clínica devueltos por la API.
    Este schema es de solo lectura: las alertas las genera el sistema,
    no el cliente.
    """

    id:            int
    resultado_id:  int
    severidad:     SeveridadAlerta
    mensaje:       str              # Texto legible: "CRÍTICO — Potasio: 7.1 mEq/L"
    notificado:    bool             # True si el email/webhook se envió con éxito
    notificado_at: Optional[datetime]
    detalle_envio: Optional[str]    # Detalle de éxito o error del envío
    created_at:    datetime

    model_config = {"from_attributes": True}


class AlertaListOut(BaseModel):
    """Listado paginado de alertas para el panel de auditoría."""

    total:   int
    alertas: list[AlertaOut]

"""
Schemas Pydantic — Muestra
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.muestra import TipoMuestra


class MuestraCreate(BaseModel):
    """
    Datos para registrar una muestra al llegar al laboratorio.
    El barcode es el código del propio tubo (diferente al de la petición).
    """

    barcode:    str
    tipo:       TipoMuestra
    peticion_id: int


class MuestraRecibida(BaseModel):
    """Payload para marcar una muestra como recibida en laboratorio."""

    recibida_at: Optional[datetime] = None  # Si no se indica, se usa la hora actual


class MuestraOut(BaseModel):
    id:           int
    barcode:      str
    tipo:         TipoMuestra
    peticion_id:  int
    recibida_at:  Optional[datetime]
    procesada_at: Optional[datetime]
    created_at:   datetime

    model_config = {"from_attributes": True}

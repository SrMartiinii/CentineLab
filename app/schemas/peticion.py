"""
Schemas Pydantic — Peticion
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.peticion import EstadoPeticion
from app.schemas.sanitario import SanitarioOut


class PeticionCreate(BaseModel):
    """
    Datos para crear una nueva petición de analítica.
    Los IDs de sanitarios vinculan la petición con los responsables del caso.
    """

    barcode:       str              # Código impreso en las etiquetas de los botes
    motivo:        Optional[str] = None
    paciente_id:   int              # FK al paciente
    enfermero_id:  int              # FK al sanitario con rol enfermero
    medico_id:     int              # FK al sanitario con rol médico


class PeticionUpdate(BaseModel):
    """Permite actualizar el estado de la petición o el motivo."""

    motivo:        Optional[str]           = None
    estado:        Optional[EstadoPeticion] = None
    enfermero_id:  Optional[int]           = None
    medico_id:     Optional[int]           = None


class PeticionOut(BaseModel):
    """Petición completa con sanitarios embebidos para comodidad del cliente."""

    id:          int
    barcode:     str
    motivo:      Optional[str]
    estado:      EstadoPeticion
    paciente_id: int
    enfermero:   SanitarioOut  # Objeto completo, no solo el ID
    medico:      SanitarioOut
    created_at:  datetime
    updated_at:  Optional[datetime]

    model_config = {"from_attributes": True}

"""
Schemas Pydantic — Paciente
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class PacienteCreate(BaseModel):
    """Datos necesarios para registrar un nuevo paciente."""

    nombre:           str
    apellidos:        str
    nhc:              str        # Número de Historia Clínica — debe ser único
    fecha_nacimiento: date
    telefono:         Optional[str]      = None
    email:            Optional[EmailStr] = None


class PacienteUpdate(BaseModel):
    """Actualización parcial: todos los campos son opcionales."""

    nombre:           Optional[str]      = None
    apellidos:        Optional[str]      = None
    fecha_nacimiento: Optional[date]     = None
    telefono:         Optional[str]      = None
    email:            Optional[EmailStr] = None


class PacienteOut(BaseModel):
    """Datos del paciente devueltos por la API."""

    id:               int
    nombre:           str
    apellidos:        str
    nhc:              str
    fecha_nacimiento: date
    telefono:         Optional[str]
    email:            Optional[str]
    created_at:       datetime

    model_config = {"from_attributes": True}

"""
Schemas Pydantic — Sanitario
Definen la forma de los datos que entran y salen de la API.
Pydantic valida automáticamente los tipos y lanza HTTP 422 si algo no cuadra.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, HttpUrl

from app.models.sanitario import RolSanitario


# ── Schemas de entrada (lo que envía el cliente) ───────────────────────────

class SanitarioCreate(BaseModel):
    """Datos necesarios para registrar un nuevo sanitario."""

    nombre:              str
    apellidos:           str
    codigo_profesional:  str           # Número de colegiado o código interno
    email:               EmailStr      # Validado automáticamente por Pydantic
    webhook_url:         Optional[HttpUrl] = None  # URL de Slack/Teams, opcional
    rol:                 RolSanitario


class SanitarioUpdate(BaseModel):
    """Todos los campos son opcionales — permite actualizar parcialmente (PATCH)."""

    nombre:     Optional[str]      = None
    apellidos:  Optional[str]      = None
    email:      Optional[EmailStr] = None
    webhook_url: Optional[HttpUrl] = None
    activo:     Optional[bool]     = None


# ── Schemas de salida (lo que devuelve la API) ─────────────────────────────

class SanitarioOut(BaseModel):
    """Representación completa de un sanitario en respuestas de la API."""

    id:                  int
    nombre:              str
    apellidos:           str
    codigo_profesional:  str
    email:               str
    webhook_url:         Optional[str]
    rol:                 RolSanitario
    activo:              bool
    created_at:          datetime

    # Permite que Pydantic lea los atributos del objeto SQLAlchemy directamente
    model_config = {"from_attributes": True}

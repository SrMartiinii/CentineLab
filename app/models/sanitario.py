"""
Modelo Sanitario
Representa a los profesionales sanitarios (enfermeros y médicos) del sistema.
Son los destinatarios de las alertas cuando un resultado es crítico.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


# Roles posibles de un sanitario en el sistema
class RolSanitario(str, enum.Enum):
    enfermero = "enfermero"  # Recibe notificaciones directas
    medico = "medico"        # Recibe copia de alertas críticas


class Sanitario(Base):
    """
    Tabla 'sanitarios' — personal que puede recibir alertas.
    Cada petición de analítica tiene un enfermero y un médico asignado.
    """

    __tablename__ = "sanitarios"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150), nullable=False)

    # Identificador profesional único (número de colegiado, código interno, etc.)
    codigo_profesional = Column(String(50), unique=True, nullable=False, index=True)

    # Email al que se enviarán las alertas por SMTP
    email = Column(String(254), unique=True, nullable=False)

    # URL opcional para webhooks (Slack, Teams, sistema hospitalario…)
    webhook_url = Column(String(500), nullable=True)

    rol = Column(Enum(RolSanitario), nullable=False)

    # Permite desactivar un sanitario sin borrarlo (baja temporal, vacaciones…)
    activo = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones inversas: peticiones en las que este sanitario es enfermero o médico
    peticiones_como_enfermero = relationship(
        "Peticion",
        foreign_keys="Peticion.enfermero_id",
        back_populates="enfermero",
    )
    peticiones_como_medico = relationship(
        "Peticion",
        foreign_keys="Peticion.medico_id",
        back_populates="medico",
    )

    def __repr__(self) -> str:
        return f"<Sanitario {self.codigo_profesional} | {self.rol.value}>"

"""
Modelo Paciente
Datos demográficos del paciente al que pertenece la analítica.
El NHC (Número de Historia Clínica) es el identificador único en el sistema.
"""

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Paciente(Base):
    """
    Tabla 'pacientes' — datos del paciente.
    Un paciente puede tener múltiples peticiones de analítica a lo largo del tiempo.
    """

    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150), nullable=False)

    # NHC: identificador único del paciente en el sistema sanitario
    nhc = Column(String(20), unique=True, nullable=False, index=True)

    fecha_nacimiento = Column(Date, nullable=False)

    # Datos de contacto opcionales (pueden usarse en notificaciones futuras)
    telefono = Column(String(20), nullable=True)
    email = Column(String(254), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relación 1-N: un paciente puede tener múltiples peticiones
    peticiones = relationship("Peticion", back_populates="paciente")

    def __repr__(self) -> str:
        return f"<Paciente NHC={self.nhc} | {self.apellidos}, {self.nombre}>"

"""
Modelo Peticion
Representa la orden de analítica generada en el centro de salud.
Contiene el código de barras que vincula físicamente los botes con el sistema,
y los sanitarios (enfermero + médico) responsables del caso.
"""

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class EstadoPeticion(str, enum.Enum):
    """Estados por los que pasa una petición en su ciclo de vida."""
    pendiente   = "pendiente"    # Petición creada, aún no extraída
    extraida    = "extraida"     # Muestra recogida, esperando análisis
    procesando  = "procesando"   # En el analizador
    completada  = "completada"   # Resultados disponibles


class Peticion(Base):
    """
    Tabla 'peticiones' — orden de analítica.
    Es el objeto central del sistema: vincula paciente, sanitarios y muestras.
    """

    __tablename__ = "peticiones"

    id = Column(Integer, primary_key=True, index=True)

    # Código de barras único impreso en las etiquetas de los botes
    # Garantiza la trazabilidad física desde la extracción hasta el laboratorio
    barcode = Column(String(100), unique=True, nullable=False, index=True)

    # Motivo clínico de la petición (e.g. "Control HbA1c", "Urgencias")
    motivo = Column(String(255), nullable=True)

    estado = Column(Enum(EstadoPeticion), default=EstadoPeticion.pendiente, nullable=False)

    # FK al paciente al que pertenece esta analítica
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)

    # Enfermero asignado: extraerá la muestra y recibirá las alertas
    enfermero_id = Column(Integer, ForeignKey("sanitarios.id"), nullable=False)

    # Médico responsable: también recibirá copia de alertas críticas
    medico_id = Column(Integer, ForeignKey("sanitarios.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relaciones ─────────────────────────────────────────────────────────
    paciente  = relationship("Paciente", back_populates="peticiones")

    enfermero = relationship(
        "Sanitario",
        foreign_keys=[enfermero_id],
        back_populates="peticiones_como_enfermero",
    )
    medico = relationship(
        "Sanitario",
        foreign_keys=[medico_id],
        back_populates="peticiones_como_medico",
    )

    # Una petición puede tener una o varias muestras (tubo de suero, EDTA, orina…)
    muestras = relationship("Muestra", back_populates="peticion")

    def __repr__(self) -> str:
        return f"<Peticion barcode={self.barcode} | {self.estado.value}>"

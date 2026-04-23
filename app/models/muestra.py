"""
Modelo Muestra
Representa el tubo físico de sangre (u otro tipo de muestra) etiquetado con
la pegatina del código de barras. Cada petición puede generar varias muestras
según los análisis solicitados (bioquímica, hematología, coagulación…).
"""

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class TipoMuestra(str, enum.Enum):
    """Tipo de material biológico recogido en el tubo."""
    suero         = "suero"          # Tubo rojo/amarillo — bioquímica
    plasma_edta   = "plasma_edta"    # Tubo morado — hematología
    plasma_citrato = "plasma_citrato" # Tubo azul — coagulación (INR…)
    sangre_total  = "sangre_total"   # Tubo verde — análisis especiales
    orina         = "orina"          # Recipiente de orina — sedimento/cultivo


class Muestra(Base):
    """
    Tabla 'muestras' — tubo físico identificado por barcode.
    Cuando llega al laboratorio, el técnico la registra como recibida.
    Cuando el analizador termina, los resultados se vinculan a esta muestra.
    """

    __tablename__ = "muestras"

    id = Column(Integer, primary_key=True, index=True)

    # Barcode propio del tubo (diferente al de la petición)
    barcode = Column(String(100), unique=True, nullable=False, index=True)

    tipo = Column(Enum(TipoMuestra), nullable=False)

    # FK a la petición que originó esta muestra
    peticion_id = Column(Integer, ForeignKey("peticiones.id"), nullable=False)

    # Timestamps de trazabilidad en laboratorio
    recibida_at   = Column(DateTime, nullable=True)   # Cuando llega al lab
    procesada_at  = Column(DateTime, nullable=True)   # Cuando sale del analizador

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relaciones ─────────────────────────────────────────────────────────
    peticion   = relationship("Peticion", back_populates="muestras")

    # Una muestra puede tener múltiples resultados (un parámetro por resultado)
    resultados = relationship("Resultado", back_populates="muestra")

    def __repr__(self) -> str:
        return f"<Muestra barcode={self.barcode} | {self.tipo.value}>"

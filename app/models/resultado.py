"""
Modelo Resultado
Almacena el valor numérico de un parámetro analítico para una muestra concreta.
Al crearse, el motor de alertas evalúa si el valor supera los rangos críticos.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Resultado(Base):
    """
    Tabla 'resultados' — valor individual de un parámetro analítico.

    Ejemplo de un resultado:
        parametro = "potasio"
        valor     = 7.1
        unidad    = "mEq/L"
        → el motor de alertas detectará que supera el umbral crítico (6.5)
    """

    __tablename__ = "resultados"

    id = Column(Integer, primary_key=True, index=True)

    # Nombre normalizado del parámetro (minúsculas, sin tildes)
    # Debe coincidir con las claves de CLINICAL_RANGES en services/clinical_ranges.py
    parametro = Column(String(100), nullable=False, index=True)

    # Valor numérico reportado por el analizador
    valor = Column(Float, nullable=False)

    # Unidad de medida (mEq/L, mg/dL, g/dL, etc.)
    unidad = Column(String(30), nullable=False)

    # FK a la muestra de la que se extrae este resultado
    muestra_id = Column(Integer, ForeignKey("muestras.id"), nullable=False)

    # Nombre del analizador o laboratorio externo que generó el valor
    fuente = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relaciones ─────────────────────────────────────────────────────────
    muestra = relationship("Muestra", back_populates="resultados")

    # Relación 1-1 con la alerta (si se generó alguna)
    alerta = relationship("Alerta", back_populates="resultado", uselist=False)

    def __repr__(self) -> str:
        return f"<Resultado {self.parametro}={self.valor} {self.unidad}>"

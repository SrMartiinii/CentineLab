"""
Modelo Alerta
Registro de cada alerta clínica generada por el motor de alertas.
Sirve como auditoría: qué se detectó, cuándo, a quién se notificó y si tuvo éxito.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class SeveridadAlerta(str, enum.Enum):
    """
    Niveles de severidad clínica.
    Determinan el canal de notificación y la urgencia:
        critica → email + webhook inmediato
        alta    → email en < 5 minutos
        media   → notificación en próxima revisión
    """
    critica = "critica"
    alta    = "alta"
    media   = "media"


class Alerta(Base):
    """
    Tabla 'alertas' — registro de cada valor clínico fuera de rango.

    Cada vez que el motor de alertas detecta un resultado crítico, crea
    una fila aquí con toda la información necesaria para la trazabilidad:
    quién fue notificado, cuándo, si el envío tuvo éxito o falló.
    """

    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)

    # FK al resultado que disparó esta alerta
    resultado_id = Column(Integer, ForeignKey("resultados.id"), unique=True, nullable=False)

    severidad = Column(Enum(SeveridadAlerta), nullable=False)

    # Mensaje human-readable generado automáticamente
    # Ejemplo: "CRÍTICO — Potasio: 7.1 mEq/L (umbral: >6.5)"
    mensaje = Column(String(500), nullable=False)

    # Estado de la notificación
    notificado    = Column(Boolean, default=False, nullable=False)
    notificado_at = Column(DateTime, nullable=True)

    # Detalle del resultado del envío (útil para depurar fallos de SMTP/webhook)
    detalle_envio = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relaciones ─────────────────────────────────────────────────────────
    resultado = relationship("Resultado", back_populates="alerta")

    def __repr__(self) -> str:
        estado = "✓" if self.notificado else "✗"
        return f"<Alerta [{self.severidad.value}] resultado_id={self.resultado_id} notif={estado}>"

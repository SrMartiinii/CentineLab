"""
Motor de alertas.

Es el núcleo clínico del sistema. Cuando se registra un resultado analítico,
este módulo:
    1. Evalúa el valor contra los rangos clínicos.
    2. Si está fuera de rango, crea una fila en la tabla `alertas`.
    3. Obtiene los datos de los sanitarios asignados a la petición.
    4. Dispara las notificaciones (email + webhook).
    5. Actualiza la alerta con el resultado del envío.

TODO:
  · Mover el procesamiento a una tarea en segundo plano (BackgroundTasks
    de FastAPI o, mejor, Celery). Hoy el endpoint bloquea hasta que
    terminan los envíos.
  · Deduplicar alertas: si el mismo parámetro se dispara varias veces en
    un corto intervalo, no hace falta enviar N emails idénticos.
  · Escalado: si una alerta crítica no se confirma como "vista" en X min,
    escalar al jefe de guardia (implica tabla de "escalation policy").
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.alerta import Alerta, SeveridadAlerta
from app.models.resultado import Resultado
from app.services.clinical_ranges import evaluar_resultado, generar_mensaje_alerta
from app.services.notifier import notificar_alerta

logger = logging.getLogger(__name__)


def procesar_resultado(resultado: Resultado, db: Session) -> Optional[Alerta]:
    """
    Procesa un resultado recién creado. Devuelve la alerta generada
    o None si el valor era normal.
    """
    # 1. Evaluar contra los rangos clínicos
    severidad = evaluar_resultado(resultado.parametro, resultado.valor)
    if severidad is None:
        return None  # Valor dentro de rango → no se hace nada

    # 2. Reunir datos del paciente y los sanitarios por la cadena de relaciones
    muestra  = resultado.muestra
    peticion = muestra.peticion
    paciente = peticion.paciente

    nombre_paciente = f"{paciente.apellidos}, {paciente.nombre}"
    mensaje = generar_mensaje_alerta(
        parametro=resultado.parametro,
        valor=resultado.valor,
        severidad=severidad,
        nombre_paciente=nombre_paciente,
    )

    logger.warning("ALERTA %s: %s", severidad.value.upper(), mensaje)

    # 3. Crear el registro de alerta (aún sin notificar)
    alerta = Alerta(
        resultado_id=resultado.id,
        severidad=severidad,
        mensaje=mensaje,
        notificado=False,
    )
    db.add(alerta)
    db.flush()  # Para tener alerta.id antes del commit

    # 4. Lanzar notificaciones por los canales del enfermero y el médico
    emails = [peticion.enfermero.email, peticion.medico.email]
    webhooks = [peticion.enfermero.webhook_url, peticion.medico.webhook_url]

    detalle = notificar_alerta(
        severidad=severidad,
        mensaje=mensaje,
        emails=emails,
        webhooks=webhooks,
    )

    # 5. Guardar el resultado del envío en la alerta (auditoría)
    alerta.notificado    = True
    alerta.notificado_at = datetime.utcnow()
    alerta.detalle_envio = detalle

    db.commit()
    db.refresh(alerta)

    return alerta

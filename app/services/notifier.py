"""
Servicio de notificaciones.

Envía las alertas clínicas por dos canales:
    - Email SMTP al enfermero y médico asignados
    - Webhook HTTP (Slack / Teams / sistema hospitalario)

Las funciones son síncronas por simplicidad. FastAPI las ejecuta en un
threadpool, así que no bloquean el event loop.

TODO importante:
  · Mover el envío a una cola asíncrona (Celery + Redis o RQ). Un SMTP lento
    no debería retrasar la respuesta HTTP de /resultados.
  · Implementar reintentos con backoff exponencial (tenacity).
  · Deduplicar: si llegan N resultados críticos del mismo paciente en pocos
    segundos, agrupar en un único email (evitar "alert fatigue").
  · Soporte de SMS como tercer canal (p. ej. Twilio) para alertas críticas
    fuera de horario laboral.
"""

import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.config import settings
from app.models.alerta import SeveridadAlerta

logger = logging.getLogger(__name__)


def enviar_email(destinatarios: list[str], asunto: str, cuerpo: str) -> str:
    """
    Envía un email en texto plano a los destinatarios indicados.
    Devuelve un string con el resultado (éxito o error) para registrarlo
    en la tabla `alertas.detalle_envio` (auditoría).

    Si no hay SMTP configurado (típico en desarrollo), escribe el email en
    los logs y devuelve "dry-run". Esto permite probar el flujo completo
    sin montar un servidor de correo.
    """
    if not settings.smtp_host:
        logger.warning(
            "[DRY-RUN] SMTP no configurado. Email NO enviado.\n"
            "  Para:    %s\n  Asunto:  %s\n  Cuerpo:  %s",
            destinatarios, asunto, cuerpo,
        )
        return "dry-run (SMTP no configurado)"

    # Construcción del mensaje
    msg = EmailMessage()
    msg["From"]    = settings.smtp_from
    msg["To"]      = ", ".join(destinatarios)
    msg["Subject"] = asunto
    msg.set_content(cuerpo)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as servidor:
            servidor.starttls()
            if settings.smtp_user:
                servidor.login(settings.smtp_user, settings.smtp_password)
            servidor.send_message(msg)

        logger.info("Email enviado a %s", destinatarios)
        return f"email OK ({len(destinatarios)} destinatarios)"

    except Exception as exc:
        # No relanzo la excepción: un fallo de SMTP no debe tumbar la API.
        # El detalle se guarda en la alerta para que un admin pueda reintentar.
        logger.error("Fallo al enviar email: %s", exc)
        return f"error email: {exc}"


def enviar_webhook(url: str, mensaje: str, severidad: SeveridadAlerta) -> str:
    """
    Envía el mensaje a un webhook externo (Slack, Teams, etc.).
    El payload usa el formato estándar de Slack Incoming Webhooks,
    compatible también con canales de Teams.
    """
    # Color del "attachment" según la severidad clínica
    colores = {
        SeveridadAlerta.critica: "danger",
        SeveridadAlerta.alta:    "warning",
        SeveridadAlerta.media:   "good",
    }

    payload = {
        "text": f"*Alerta CentineLab* — {severidad.value.upper()}",
        "attachments": [{
            "color": colores.get(severidad, "good"),
            "text":  mensaje,
            "footer": "CentineLab",
        }],
    }

    try:
        respuesta = httpx.post(url, json=payload, timeout=5.0)
        respuesta.raise_for_status()
        return f"webhook OK (HTTP {respuesta.status_code})"
    except Exception as exc:
        logger.error("Fallo al enviar webhook: %s", exc)
        return f"error webhook: {exc}"


def notificar_alerta(
    *,
    severidad: SeveridadAlerta,
    mensaje:   str,
    emails:    list[str],
    webhooks:  list[str],
) -> str:
    """
    Punto único de entrada para enviar una alerta por todos los canales
    configurados. Devuelve un resumen de los envíos que se guarda en BBDD.
    """
    asunto = f"[CentineLab] Alerta {severidad.value.upper()}"
    resultados: list[str] = []

    # Email
    emails = [e for e in emails if e]
    if emails:
        resultados.append(enviar_email(emails, asunto, mensaje))

    # Webhooks
    for url in webhooks:
        if url:
            resultados.append(enviar_webhook(url, mensaje, severidad))

    if not resultados:
        return "sin canales configurados"

    return " | ".join(resultados)

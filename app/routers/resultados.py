"""
Endpoints del flujo de laboratorio: muestras, resultados y alertas.

Este módulo agrupa tres routers porque forman un único flujo clínico:
    muestra recibida → resultado analítico → alerta (si procede)

TODO:
  · Endpoint para importar resultados en lote (integración con analizadores).
  · Endpoint para reenviar una alerta que falló en la notificación.
  · Websocket para push en tiempo real a un panel clínico.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alerta import Alerta
from app.models.muestra import Muestra
from app.models.resultado import Resultado
from app.schemas.alerta import AlertaListOut, AlertaOut
from app.schemas.muestra import MuestraCreate, MuestraOut, MuestraRecibida
from app.schemas.resultado import ResultadoCreate, ResultadoOut
from app.services.alert_engine import procesar_resultado


# ── Router de muestras ─────────────────────────────────────────────────────

muestras_router = APIRouter(prefix="/muestras", tags=["Muestras"])


@muestras_router.post("/", response_model=MuestraOut, status_code=status.HTTP_201_CREATED)
def registrar_muestra(datos: MuestraCreate, db: Session = Depends(get_db)):
    """Registra un tubo al llegar al laboratorio."""
    if db.query(Muestra).filter(Muestra.barcode == datos.barcode).first():
        raise HTTPException(409, f"Ya existe una muestra con barcode '{datos.barcode}'.")

    muestra = Muestra(**datos.model_dump())
    db.add(muestra)
    db.commit()
    db.refresh(muestra)
    return muestra


@muestras_router.patch("/{muestra_id}/recibida", response_model=MuestraOut)
def marcar_recibida(
    muestra_id: int,
    datos: MuestraRecibida,
    db: Session = Depends(get_db),
):
    """Marca la muestra como recibida. Si no se indica fecha, se usa la actual."""
    muestra = db.get(Muestra, muestra_id)
    if not muestra:
        raise HTTPException(404, "Muestra no encontrada.")

    muestra.recibida_at = datos.recibida_at or datetime.utcnow()
    db.commit()
    db.refresh(muestra)
    return muestra


@muestras_router.get("/{muestra_id}", response_model=MuestraOut)
def obtener_muestra(muestra_id: int, db: Session = Depends(get_db)):
    muestra = db.get(Muestra, muestra_id)
    if not muestra:
        raise HTTPException(404, "Muestra no encontrada.")
    return muestra


# ── Router de resultados ───────────────────────────────────────────────────

resultados_router = APIRouter(prefix="/resultados", tags=["Resultados"])


@resultados_router.post("/", response_model=ResultadoOut, status_code=status.HTTP_201_CREATED)
def registrar_resultado(datos: ResultadoCreate, db: Session = Depends(get_db)):
    """
    Registra un valor analítico y dispara el motor de alertas.

    Este es el endpoint crítico del sistema: si el valor es anómalo,
    se crea automáticamente la alerta y se envían las notificaciones.
    """
    if not db.get(Muestra, datos.muestra_id):
        raise HTTPException(404, "Muestra no encontrada.")

    resultado = Resultado(**datos.model_dump())
    db.add(resultado)
    db.commit()
    db.refresh(resultado)

    # Procesamos la alerta. Si falla el envío, el resultado YA está guardado:
    # la alerta quedará con notificado=False para reintentar más tarde.
    # TODO: mover a BackgroundTasks para no bloquear la respuesta HTTP.
    try:
        procesar_resultado(resultado, db)
        db.refresh(resultado)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error(
            "Error procesando alerta para resultado %s: %s", resultado.id, exc
        )

    return resultado


@resultados_router.get("/{resultado_id}", response_model=ResultadoOut)
def obtener_resultado(resultado_id: int, db: Session = Depends(get_db)):
    resultado = db.get(Resultado, resultado_id)
    if not resultado:
        raise HTTPException(404, "Resultado no encontrado.")
    return resultado


@resultados_router.get("/muestra/{muestra_id}", response_model=list[ResultadoOut])
def resultados_de_muestra(muestra_id: int, db: Session = Depends(get_db)):
    """Todos los resultados analíticos de una muestra concreta."""
    if not db.get(Muestra, muestra_id):
        raise HTTPException(404, "Muestra no encontrada.")
    return db.query(Resultado).filter(Resultado.muestra_id == muestra_id).all()


# ── Router de alertas ──────────────────────────────────────────────────────

alertas_router = APIRouter(prefix="/alertas", tags=["Alertas"])


@alertas_router.get("/", response_model=AlertaListOut)
def listar_alertas(
    solo_no_notificadas: bool = False,
    db: Session = Depends(get_db),
):
    """Panel de auditoría de alertas. Útil para detectar fallos de notificación."""
    query = db.query(Alerta)
    if solo_no_notificadas:
        query = query.filter(Alerta.notificado == False)  # noqa: E712
    total   = query.count()
    alertas = query.order_by(Alerta.created_at.desc()).all()
    return AlertaListOut(total=total, alertas=alertas)


@alertas_router.get("/{alerta_id}", response_model=AlertaOut)
def obtener_alerta(alerta_id: int, db: Session = Depends(get_db)):
    alerta = db.get(Alerta, alerta_id)
    if not alerta:
        raise HTTPException(404, "Alerta no encontrada.")
    return alerta

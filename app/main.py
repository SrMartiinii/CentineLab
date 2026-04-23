"""
Punto de entrada de la aplicación.
Inicializa FastAPI, registra los routers y crea las tablas al arrancar.

TODO:
  · Sustituir crear_tablas() por migraciones Alembic (no usar create_all en prod).
  · Añadir middleware de autenticación (JWT) para proteger los endpoints.
  · Configurar CORS con lista blanca de orígenes en producción.
  · Integrar Sentry o similar para captura de errores.
"""

import logging

from fastapi import FastAPI

from app.config import settings
from app.database import crear_tablas
from app.routers.pacientes import router as pacientes_router
from app.routers.peticiones import router as peticiones_router
from app.routers.resultados import alertas_router, muestras_router, resultados_router
from app.routers.sanitarios import router as sanitarios_router


# Logging básico. En producción convendría configuración estructurada (JSON).
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s — %(message)s",
)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Sistema backend de vigilancia clínica: detecta valores críticos en "
        "analíticas de sangre y notifica automáticamente al personal sanitario."
    ),
)


@app.on_event("startup")
def on_startup() -> None:
    """Crea las tablas si no existen. Reemplazar por Alembic en producción."""
    crear_tablas()


# Todos los endpoints bajo /api/v1/ para permitir versionado futuro
API_PREFIX = "/api/v1"
app.include_router(sanitarios_router, prefix=API_PREFIX)
app.include_router(pacientes_router,  prefix=API_PREFIX)
app.include_router(peticiones_router, prefix=API_PREFIX)
app.include_router(muestras_router,   prefix=API_PREFIX)
app.include_router(resultados_router, prefix=API_PREFIX)
app.include_router(alertas_router,    prefix=API_PREFIX)


@app.get("/", tags=["Root"])
def raiz():
    """Info básica de la API."""
    return {
        "app":     settings.app_name,
        "version": settings.app_version,
        "docs":    "/docs",
    }


@app.get("/health", tags=["Root"])
def health_check():
    """Endpoint de salud para monitorización."""
    return {"status": "ok"}

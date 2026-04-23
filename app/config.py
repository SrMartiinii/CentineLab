"""
Configuración de la aplicación.
Lee variables del archivo .env (o del entorno) y las expone como objeto `settings`.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de configuración del sistema."""

    # ── General ─────────────────────────────────────────────────────────
    app_name:    str  = "CentineLab"
    app_version: str  = "0.2.0"
    debug:       bool = False

    # ── Base de datos ───────────────────────────────────────────────────
    # Por defecto SQLite local para desarrollo.
    # En producción, cambiar a PostgreSQL vía variable de entorno.
    database_url: str = "sqlite:///./centinelab.db"

    # ── SMTP ────────────────────────────────────────────────────────────
    # Si smtp_host está vacío, los emails se imprimen por consola en lugar
    # de enviarse (modo desarrollo). Ver app/services/notifier.py
    smtp_host:     str = ""
    smtp_port:     int = 587
    smtp_user:     str = ""
    smtp_password: str = ""
    smtp_from:     str = "centinelab@hospital.local"

    # TODO: añadir configuración de seguridad cuando se implemente auth
    #   - JWT secret
    #   - Tiempo de expiración de tokens
    #   - CORS origins permitidos en producción

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Instancia global de configuración
settings = Settings()

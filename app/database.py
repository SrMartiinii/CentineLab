"""
Configuración de la base de datos — SQLAlchemy
Gestiona el engine, las sesiones y la dependencia de FastAPI (get_db).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


# ── Engine ─────────────────────────────────────────────────────────────────
# connect_args solo necesario para SQLite: permite el acceso desde múltiples hilos
# (FastAPI usa un threadpool para las dependencias síncronas)
_connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    # echo=True  ← descomentar para ver el SQL generado en desarrollo
)

# ── SessionLocal ──────────────────────────────────────────────────────────
# Fábrica de sesiones: cada request de la API abre una sesión nueva
# autocommit=False → los cambios se confirman manualmente con db.commit()
# autoflush=False  → evita flushes implícitos que pueden causar efectos inesperados
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Base declarativa ───────────────────────────────────────────────────────
# Todos los modelos heredan de esta clase para registrarse en los metadatos
class Base(DeclarativeBase):
    pass


# ── Dependencia FastAPI ────────────────────────────────────────────────────

def get_db():
    """
    Generador de sesión de base de datos para inyección de dependencias.

    Uso en un endpoint:
        def mi_endpoint(db: Session = Depends(get_db)): ...

    El bloque try/finally garantiza que la sesión se cierre siempre,
    incluso si el endpoint lanza una excepción.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def crear_tablas() -> None:
    """Crea todas las tablas en la base de datos si no existen aún."""
    # Importar modelos aquí para que estén registrados en Base.metadata
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

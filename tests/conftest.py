"""
Fixtures compartidos para los tests.
Usa SQLite en memoria para aislar cada test de los demás.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.muestra import Muestra, TipoMuestra
from app.models.paciente import Paciente
from app.models.peticion import Peticion
from app.models.sanitario import RolSanitario, Sanitario


# BBDD en memoria compartida por todas las conexiones del test.
# StaticPool evita que SQLite cree una BBDD nueva por cada conexión del pool.
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture
def db():
    """Sesión limpia con todas las tablas creadas."""
    import app.models  # noqa: F401  — registra los modelos en Base.metadata
    Base.metadata.create_all(bind=test_engine)

    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db):
    """Cliente HTTP de FastAPI que usa la BBDD del fixture `db`."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Datos de prueba reutilizables ──────────────────────────────────────────

@pytest.fixture
def enfermero(db):
    s = Sanitario(
        nombre="Ana",
        apellidos="García López",
        codigo_profesional="ENF-001",
        email="ana@hospital.example.com",
        rol=RolSanitario.enfermero,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture
def medico(db):
    s = Sanitario(
        nombre="Carlos",
        apellidos="Martínez Ruiz",
        codigo_profesional="MED-001",
        email="carlos@hospital.example.com",
        rol=RolSanitario.medico,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture
def paciente(db):
    p = Paciente(
        nombre="Juan",
        apellidos="Pérez Sánchez",
        nhc="NHC-TEST-001",
        fecha_nacimiento=date(1980, 5, 15),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def peticion(db, paciente, enfermero, medico):
    p = Peticion(
        barcode="TEST-BC-001",
        motivo="Analítica de control",
        paciente_id=paciente.id,
        enfermero_id=enfermero.id,
        medico_id=medico.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def muestra(db, peticion):
    m = Muestra(
        barcode="TUBO-TEST-001",
        tipo=TipoMuestra.suero,
        peticion_id=peticion.id,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

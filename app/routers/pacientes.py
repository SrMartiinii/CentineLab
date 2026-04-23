"""
Router Pacientes — /api/v1/pacientes
CRUD de pacientes. El NHC es el identificador de búsqueda principal.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.paciente import Paciente
from app.schemas.paciente import PacienteCreate, PacienteOut, PacienteUpdate

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.post("/", response_model=PacienteOut, status_code=status.HTTP_201_CREATED)
def crear_paciente(datos: PacienteCreate, db: Session = Depends(get_db)):
    """Registra un nuevo paciente. Devuelve 409 si el NHC ya existe."""
    if db.query(Paciente).filter(Paciente.nhc == datos.nhc).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un paciente con NHC '{datos.nhc}'.",
        )

    paciente = Paciente(**datos.model_dump())
    db.add(paciente)
    db.commit()
    db.refresh(paciente)
    return paciente


@router.get("/", response_model=List[PacienteOut])
def listar_pacientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista todos los pacientes con paginación básica."""
    return db.query(Paciente).offset(skip).limit(limit).all()


@router.get("/nhc/{nhc}", response_model=PacienteOut)
def buscar_por_nhc(nhc: str, db: Session = Depends(get_db)):
    """Busca un paciente por su Número de Historia Clínica (NHC)."""
    paciente = db.query(Paciente).filter(Paciente.nhc == nhc).first()
    if not paciente:
        raise HTTPException(status_code=404, detail=f"Paciente con NHC '{nhc}' no encontrado.")
    return paciente


@router.get("/{paciente_id}", response_model=PacienteOut)
def obtener_paciente(paciente_id: int, db: Session = Depends(get_db)):
    """Obtiene un paciente por su ID interno."""
    paciente = db.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
    return paciente


@router.patch("/{paciente_id}", response_model=PacienteOut)
def actualizar_paciente(
    paciente_id: int,
    datos: PacienteUpdate,
    db: Session = Depends(get_db),
):
    """Actualización parcial de datos del paciente."""
    paciente = db.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)
    return paciente

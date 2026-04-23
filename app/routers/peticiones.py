"""
Endpoints de peticiones de analítica.

Una petición es la "orden" que se genera en consulta o urgencias y que
acompaña al paciente hasta el laboratorio. Vincula paciente, sanitarios
responsables y las muestras que se extraen.

TODO:
  · Filtro por rango de fechas (útil para auditorías).
  · Permitir añadir observaciones/notas del sanitario.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.paciente import Paciente
from app.models.peticion import EstadoPeticion, Peticion
from app.models.sanitario import RolSanitario, Sanitario
from app.schemas.peticion import PeticionCreate, PeticionOut, PeticionUpdate

router = APIRouter(prefix="/peticiones", tags=["Peticiones"])


@router.post("/", response_model=PeticionOut, status_code=status.HTTP_201_CREATED)
def crear_peticion(datos: PeticionCreate, db: Session = Depends(get_db)):
    """Crea una nueva petición. Valida paciente, sanitarios y roles."""
    # Barcode único
    if db.query(Peticion).filter(Peticion.barcode == datos.barcode).first():
        raise HTTPException(409, f"Ya existe una petición con barcode '{datos.barcode}'.")

    # Paciente existe
    if not db.get(Paciente, datos.paciente_id):
        raise HTTPException(404, "Paciente no encontrado.")

    # Enfermero: existe, activo, rol correcto
    enfermero = db.get(Sanitario, datos.enfermero_id)
    if not enfermero:
        raise HTTPException(404, "Enfermero no encontrado.")
    if not enfermero.activo:
        raise HTTPException(400, "El enfermero está inactivo.")
    if enfermero.rol != RolSanitario.enfermero:
        raise HTTPException(400, "El sanitario indicado no tiene rol de enfermero.")

    # Médico: existe, activo, rol correcto
    medico = db.get(Sanitario, datos.medico_id)
    if not medico:
        raise HTTPException(404, "Médico no encontrado.")
    if not medico.activo:
        raise HTTPException(400, "El médico está inactivo.")
    if medico.rol != RolSanitario.medico:
        raise HTTPException(400, "El sanitario indicado no tiene rol de médico.")

    peticion = Peticion(**datos.model_dump())
    db.add(peticion)
    db.commit()
    db.refresh(peticion)
    return peticion


@router.get("/", response_model=list[PeticionOut])
def listar_peticiones(
    paciente_id: Optional[int] = None,
    estado: Optional[EstadoPeticion] = None,
    db: Session = Depends(get_db),
):
    """Lista peticiones. Filtros opcionales por paciente y estado."""
    query = db.query(Peticion)
    if paciente_id:
        query = query.filter(Peticion.paciente_id == paciente_id)
    if estado:
        query = query.filter(Peticion.estado == estado)
    return query.order_by(Peticion.created_at.desc()).all()


@router.get("/barcode/{barcode}", response_model=PeticionOut)
def buscar_por_barcode(barcode: str, db: Session = Depends(get_db)):
    """Busca una petición por código de barras (uso: pistolas lectoras en lab)."""
    peticion = db.query(Peticion).filter(Peticion.barcode == barcode).first()
    if not peticion:
        raise HTTPException(404, f"Petición con barcode '{barcode}' no encontrada.")
    return peticion


@router.get("/{peticion_id}", response_model=PeticionOut)
def obtener_peticion(peticion_id: int, db: Session = Depends(get_db)):
    peticion = db.get(Peticion, peticion_id)
    if not peticion:
        raise HTTPException(404, "Petición no encontrada.")
    return peticion


@router.patch("/{peticion_id}", response_model=PeticionOut)
def actualizar_peticion(
    peticion_id: int,
    datos: PeticionUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza campos de la petición (típicamente el estado)."""
    peticion = db.get(Peticion, peticion_id)
    if not peticion:
        raise HTTPException(404, "Petición no encontrada.")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(peticion, campo, valor)

    db.commit()
    db.refresh(peticion)
    return peticion

"""
Endpoints de gestión de personal sanitario.

TODO:
  · Añadir autenticación: solo admins deberían crear/borrar sanitarios.
  · Endpoint de búsqueda por nombre/apellidos.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sanitario import Sanitario
from app.schemas.sanitario import SanitarioCreate, SanitarioOut, SanitarioUpdate

router = APIRouter(prefix="/sanitarios", tags=["Sanitarios"])


@router.post("/", response_model=SanitarioOut, status_code=status.HTTP_201_CREATED)
def crear_sanitario(datos: SanitarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo profesional sanitario."""
    # Comprobar que no exista ya por código profesional o por email
    duplicado = db.query(Sanitario).filter(
        (Sanitario.codigo_profesional == datos.codigo_profesional) |
        (Sanitario.email == datos.email)
    ).first()
    if duplicado:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un sanitario con ese código profesional o email.",
        )

    sanitario = Sanitario(**datos.model_dump())
    db.add(sanitario)
    db.commit()
    db.refresh(sanitario)
    return sanitario


@router.get("/", response_model=list[SanitarioOut])
def listar_sanitarios(
    activo: bool | None = None,
    db: Session = Depends(get_db),
):
    """Lista sanitarios. Permite filtrar por activo=true/false."""
    query = db.query(Sanitario)
    if activo is not None:
        query = query.filter(Sanitario.activo == activo)
    return query.all()


@router.get("/{sanitario_id}", response_model=SanitarioOut)
def obtener_sanitario(sanitario_id: int, db: Session = Depends(get_db)):
    sanitario = db.get(Sanitario, sanitario_id)
    if not sanitario:
        raise HTTPException(status_code=404, detail="Sanitario no encontrado.")
    return sanitario


@router.patch("/{sanitario_id}", response_model=SanitarioOut)
def actualizar_sanitario(
    sanitario_id: int,
    datos: SanitarioUpdate,
    db: Session = Depends(get_db),
):
    """Actualización parcial: solo se modifican los campos enviados."""
    sanitario = db.get(Sanitario, sanitario_id)
    if not sanitario:
        raise HTTPException(status_code=404, detail="Sanitario no encontrado.")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(sanitario, campo, valor)

    db.commit()
    db.refresh(sanitario)
    return sanitario


@router.delete("/{sanitario_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_sanitario(sanitario_id: int, db: Session = Depends(get_db)):
    """
    Marca el sanitario como inactivo en vez de borrarlo físicamente.
    Así se preserva la integridad referencial con peticiones antiguas.
    """
    sanitario = db.get(Sanitario, sanitario_id)
    if not sanitario:
        raise HTTPException(status_code=404, detail="Sanitario no encontrado.")

    sanitario.activo = False
    db.commit()

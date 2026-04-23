"""
Punto de entrada de los modelos SQLAlchemy.
Importar desde aquí garantiza que todas las tablas estén registradas
en Base.metadata antes de llamar a Base.metadata.create_all().
"""

from app.models.alerta import Alerta, SeveridadAlerta
from app.models.muestra import Muestra, TipoMuestra
from app.models.paciente import Paciente
from app.models.peticion import EstadoPeticion, Peticion
from app.models.resultado import Resultado
from app.models.sanitario import RolSanitario, Sanitario

__all__ = [
    "Sanitario", "RolSanitario",
    "Paciente",
    "Peticion", "EstadoPeticion",
    "Muestra", "TipoMuestra",
    "Resultado",
    "Alerta", "SeveridadAlerta",
]

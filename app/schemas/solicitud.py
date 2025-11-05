from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SolicitudCreate(BaseModel):
    tipo_material: str
    cantidad: float
    descripcion: Optional[str] = None
    latitud: float
    longitud: float
    direccion: Optional[str] = None

class SolicitudOut(BaseModel):
    id: int
    usuario_id: int
    reciclador_id: Optional[int] = None
    tipo_material: str
    cantidad: float
    descripcion: Optional[str] = None
    latitud: float
    longitud: float
    direccion: Optional[str] = None
    estado: str
    fecha_solicitud: datetime
    fecha_aceptacion: Optional[datetime] = None
    fecha_completado: Optional[datetime] = None

    class Config:
        from_attributes = True
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SolicitudCreate(BaseModel):
    usuario_id: int
    direccion: str
    latitud: float
    longitud: float

class SolicitudOut(BaseModel):
    id: int
    direccion: str
    latitud: float
    longitud: float
    estado: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime
import enum
from sqlalchemy.types import Enum as SQLEnum

class EstadoSolicitud(str, enum.Enum):
    pendiente = "pendiente"
    aceptada = "aceptada"
    en_camino = "en_camino"
    completada = "completada"
    cancelada = "cancelada"

class Solicitud(Base):
    __tablename__ = "solicitudes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    reciclador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tipo_material = Column(String)
    cantidad = Column(Float)
    descripcion = Column(String, nullable=True)
    
    # Geolocalización
    latitud = Column(Float)
    longitud = Column(Float)
    direccion = Column(String)
    
    estado = Column(SQLEnum(EstadoSolicitud), default=EstadoSolicitud.pendiente)
    fecha_solicitud = Column(DateTime)
    fecha_aceptacion = Column(DateTime, nullable=True)
    fecha_completado = Column(DateTime, nullable=True)

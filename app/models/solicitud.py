from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

class Solicitud(Base):
    __tablename__ = "solicitudes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    direccion = Column(String, nullable=False)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    estado = Column(String, default="pendiente")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario")

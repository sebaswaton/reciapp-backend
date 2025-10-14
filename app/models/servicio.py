from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id"))
    reciclador_id = Column(Integer, ForeignKey("usuarios.id"))
    estado = Column(String, default="asignado")
    fecha_inicio = Column(DateTime, default=datetime.utcnow)
    fecha_fin = Column(DateTime, nullable=True)

    solicitud = relationship("Solicitud")
    reciclador = relationship("Usuario")

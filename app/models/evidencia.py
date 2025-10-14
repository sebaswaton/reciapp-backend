from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.models.base import Base

class Evidencia(Base):
    __tablename__ = "evidencias"

    id = Column(Integer, primary_key=True, index=True)
    servicio_id = Column(Integer, ForeignKey("servicios.id"))
    foto_url = Column(String, nullable=False)
    peso_kg = Column(Float, nullable=False)
    latitud = Column(Float)
    longitud = Column(Float)

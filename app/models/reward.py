from sqlalchemy import Column, Integer, String, Float
from app.models.base import Base

class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    costo_puntos = Column(Float, nullable=False)

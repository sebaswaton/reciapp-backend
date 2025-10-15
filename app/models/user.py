from sqlalchemy import Column, Integer, String
from app.models.base import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(120), unique=True, index=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False)

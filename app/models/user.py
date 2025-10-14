from sqlalchemy import Column, Integer, String, Enum
from app.models.base import Base
import enum

class RolUsuario(str,enum.Enum):
    ciudadano = "ciudadano"
    reciclador = "reciclador"
    admin = "admin"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    contrasena = Column(String, nullable=False)
    rol = Column(Enum(RolUsuario), nullable=False)
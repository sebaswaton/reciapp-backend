from pydantic import BaseModel, EmailStr
from enum import Enum

class RolUsuario(str, Enum):
    ciudadano = "ciudadano"
    reciclador = "reciclador"
    admin = "admin"

class UsuarioCreate(BaseModel):
    nombre: str
    correo: EmailStr
    contrasena: str
    rol: RolUsuario

class UsuarioOut(BaseModel):
    id: int
    nombre: str
    correo: EmailStr
    rol: RolUsuario

    class Config:
        from_attributes = True

class UsuarioLogin(BaseModel):
    correo: EmailStr
    contrasena: str
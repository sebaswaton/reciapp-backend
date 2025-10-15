from pydantic import BaseModel
from typing import Optional

class RewardBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    costo_puntos: float

class RewardCreate(RewardBase):
    pass

class RewardOut(RewardBase):
    id: int

    class Config:
        orm_mode = True  # ✅ usa 'orm_mode' para Pydantic v1 (Python 3.9)

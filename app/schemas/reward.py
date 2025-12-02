from pydantic import BaseModel, ConfigDict
from typing import Optional

class RewardBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    costo_puntos: float

class RewardCreate(RewardBase):
    stock: int = 0

class RewardOut(RewardBase):
    id: int
    stock: int

    model_config = ConfigDict(from_attributes=True)

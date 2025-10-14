from sqlalchemy import Column, Integer, ForeignKey, Float
from app.models.base import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True)
    puntos = Column(Float, default=0.0)

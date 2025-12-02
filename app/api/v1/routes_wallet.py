from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.api.v1.routes_auth import get_current_user

router = APIRouter()

@router.get("/wallets/{usuario_id}")
def get_wallet(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener wallet de un usuario.
    Si no existe, crear uno automáticamente.
    """
    # Verificar que el usuario existe
    usuario = db.query(User).filter(User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Buscar o crear wallet
    wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario_id).first()
    
    if not wallet:
        wallet = Wallet(
            usuario_id=usuario_id,
            puntos=0,
            saldo=0.0
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    return {
        "id": wallet.id,
        "usuario_id": wallet.usuario_id,
        "puntos": wallet.puntos,
        "saldo": wallet.saldo,
        "fecha_creacion": wallet.fecha_creacion
    }

@router.post("/wallets/{usuario_id}/puntos")
def agregar_puntos(
    usuario_id: int,
    puntos: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Agregar puntos al wallet de un usuario.
    """
    wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario_id).first()
    
    if not wallet:
        wallet = Wallet(usuario_id=usuario_id, puntos=puntos, saldo=0.0)
        db.add(wallet)
    else:
        wallet.puntos += puntos
    
    db.commit()
    db.refresh(wallet)
    
    return {
        "mensaje": f"Se agregaron {puntos} puntos",
        "puntos_totales": wallet.puntos
    }

@router.post("/wallets/{usuario_id}/canjear")
def canjear_puntos(
    usuario_id: int,
    puntos_a_canjear: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Canjear puntos por recompensas.
    """
    wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario_id).first()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrado")
    
    if wallet.puntos < puntos_a_canjear:
        raise HTTPException(status_code=400, detail="Puntos insuficientes")
    
    wallet.puntos -= puntos_a_canjear
    db.commit()
    db.refresh(wallet)
    
    return {
        "mensaje": f"Canjeaste {puntos_a_canjear} puntos",
        "puntos_restantes": wallet.puntos
    }

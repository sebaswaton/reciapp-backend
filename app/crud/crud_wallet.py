from sqlalchemy.orm import Session
from app.models.wallet import Wallet

def create_wallet(db: Session, usuario_id: int):
    db_wallet = Wallet(usuario_id=usuario_id, puntos=0.0)
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)
    return db_wallet

def get_wallet(db: Session, usuario_id: int):
    return db.query(Wallet).filter(Wallet.usuario_id == usuario_id).first()

def update_wallet(db: Session, usuario_id: int, puntos: float):
    wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario_id).first()
    if wallet:
        wallet.puntos += puntos
        db.commit()
        db.refresh(wallet)
    return wallet

def delete_wallet(db: Session, usuario_id: int):
    wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario_id).first()
    if wallet:
        db.delete(wallet)
        db.commit()
    return wallet

def redeem_points(db: Session, usuario_id: int, puntos: float):
    wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario_id).first()
    if not wallet:
        return None
    if wallet.puntos < puntos:
        return "INSUFFICIENT_POINTS"
    wallet.puntos -= puntos
    db.commit()
    db.refresh(wallet)
    return wallet


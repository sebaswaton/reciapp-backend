from sqlalchemy.orm import Session
from app.models.evidencia import Evidencia

def create_evidencia(db: Session, evidencia_data: dict):
    db_evidencia = Evidencia(**evidencia_data)
    db.add(db_evidencia)
    db.commit()
    db.refresh(db_evidencia)
    return db_evidencia

def get_evidencia(db: Session, evidencia_id: int):
    return db.query(Evidencia).filter(Evidencia.id == evidencia_id).first()

def get_evidencias(db: Session):
    return db.query(Evidencia).all()

def delete_evidencia(db: Session, evidencia_id: int):
    evidencia = db.query(Evidencia).filter(Evidencia.id == evidencia_id).first()
    if evidencia:
        db.delete(evidencia)
        db.commit()
    return evidencia

from sqlalchemy.orm import Session
from app.models.solicitud import Solicitud
from app.schemas.solicitud import SolicitudCreate

def create_solicitud(db: Session, solicitud: SolicitudCreate):
    db_solicitud = Solicitud(**solicitud.model_dump())
    db.add(db_solicitud)
    db.commit()
    db.refresh(db_solicitud)
    return db_solicitud

def get_solicitud(db: Session, solicitud_id: int):
    return db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()

def get_solicitudes(db: Session):
    return db.query(Solicitud).all()

def update_solicitud(db: Session, solicitud_id: int, nuevos_datos: dict):
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if solicitud:
        for key, value in nuevos_datos.items():
            setattr(solicitud, key, value)
        db.commit()
        db.refresh(solicitud)
    return solicitud

def delete_solicitud(db: Session, solicitud_id: int):
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if solicitud:
        db.delete(solicitud)
        db.commit()
    return solicitud

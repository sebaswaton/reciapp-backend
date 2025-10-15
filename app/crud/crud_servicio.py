from sqlalchemy.orm import Session
from app.models.servicio import Servicio

def create_servicio(db: Session, servicio_data: dict):
    db_servicio = Servicio(**servicio_data)
    db.add(db_servicio)
    db.commit()
    db.refresh(db_servicio)
    return db_servicio

def get_servicio(db: Session, servicio_id: int):
    return db.query(Servicio).filter(Servicio.id == servicio_id).first()

def get_servicios(db: Session):
    return db.query(Servicio).all()

def update_servicio(db: Session, servicio_id: int, nuevos_datos: dict):
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if servicio:
        for key, value in nuevos_datos.items():
            setattr(servicio, key, value)
        db.commit()
        db.refresh(servicio)
    return servicio

def delete_servicio(db: Session, servicio_id: int):
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if servicio:
        db.delete(servicio)
        db.commit()
    return servicio

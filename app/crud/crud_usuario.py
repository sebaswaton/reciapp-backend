from sqlalchemy.orm import Session
from app.models.user import Usuario
from app.schemas.user import UsuarioCreate

def create_usuario(db: Session, usuario: UsuarioCreate):
    db_usuario = Usuario(**usuario.model_dump())
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def get_usuario(db: Session, usuario_id: int):
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()

def get_usuario_by_correo(db: Session, correo: str):
    return db.query(Usuario).filter(Usuario.correo == correo).first()

def get_usuarios(db: Session):
    return db.query(Usuario).all()

def update_usuario(db: Session, usuario_id: int, nuevos_datos: dict):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        for key, value in nuevos_datos.items():
            setattr(usuario, key, value)
        db.commit()
        db.refresh(usuario)
    return usuario

def delete_usuario(db: Session, usuario_id: int):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        db.delete(usuario)
        db.commit()
    return usuario

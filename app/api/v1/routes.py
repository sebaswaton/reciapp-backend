from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import user as models_user, solicitud as models_solicitud
from app.schemas import user as schemas_user, solicitud as schemas_solicitud

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- Usuarios --------------------

@router.post("/usuarios", response_model=schemas_user.UsuarioOut)
def crear_usuario(usuario: schemas_user.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = models_user.Usuario(**usuario.dict())
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.get("/usuarios", response_model=list[schemas_user.UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(models_user.Usuario).all()

# -------------------- Solicitudes --------------------

@router.post("/solicitudes", response_model=schemas_solicitud.SolicitudOut)
def crear_solicitud(solicitud: schemas_solicitud.SolicitudCreate, db: Session = Depends(get_db)):
    db_solicitud = models_solicitud.Solicitud(**solicitud.dict())
    db.add(db_solicitud)
    db.commit()
    db.refresh(db_solicitud)
    return db_solicitud

@router.get("/solicitudes", response_model=list[schemas_solicitud.SolicitudOut])
def listar_solicitudes(db: Session = Depends(get_db)):
    return db.query(models_solicitud.Solicitud).all()

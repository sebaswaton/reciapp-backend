from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.db.session import SessionLocal
from app.schemas import user as schemas_user
from app.models.user import Usuario
from app.core.security import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=schemas_user.UsuarioOut)
def register(usuario: schemas_user.UsuarioCreate, db: Session = Depends(get_db)):
    existing_user = db.query(Usuario).filter(Usuario.correo == usuario.correo).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    hashed_password = get_password_hash(usuario.contrasena)
    nuevo_usuario = Usuario(nombre=usuario.nombre, correo=usuario.correo, contrasena=hashed_password, rol=usuario.rol)
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@router.post("/login")
def login(form_data: schemas_user.UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.correo == form_data.correo).first()
    if not usuario or not verify_password(form_data.contrasena, usuario.contrasena):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(usuario.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

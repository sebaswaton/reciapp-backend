from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.user import Usuario
from app.db.session import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id: str = payload.get("sub")  # ← Cambiar nombre de variable
        if usuario_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Buscar por ID en lugar de correo
    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()  # ← CAMBIO AQUÍ
    if usuario is None:
        raise credentials_exception
    return usuario

def require_role(role: str):
    def role_checker(current_user: Usuario = Depends(get_current_user)):
        if current_user.rol != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Solo los usuarios con rol '{role}' pueden acceder a esta ruta"
            )
        return current_user
    return role_checker
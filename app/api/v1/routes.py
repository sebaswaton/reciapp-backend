from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas import user as schemas_user, solicitud as schemas_solicitud
from app.crud import crud_usuario, crud_solicitud, crud_servicio, crud_evidencia, crud_wallet

router = APIRouter()

# -------------------- DEPENDENCIA DE BD --------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===========================================================
# 🧍‍♂️ USUARIOS
# ===========================================================

@router.post("/usuarios", response_model=schemas_user.UsuarioOut)
def crear_usuario(usuario: schemas_user.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = crud_usuario.get_usuario_by_correo(db, usuario.correo)
    if db_usuario:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return crud_usuario.create_usuario(db, usuario)

@router.get("/usuarios", response_model=list[schemas_user.UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return crud_usuario.get_usuarios(db)

@router.get("/usuarios/{usuario_id}", response_model=schemas_user.UsuarioOut)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = crud_usuario.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.put("/usuarios/{usuario_id}", response_model=schemas_user.UsuarioOut)
def actualizar_usuario(usuario_id: int, usuario_data: dict, db: Session = Depends(get_db)):
    usuario = crud_usuario.update_usuario(db, usuario_id, usuario_data)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.delete("/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = crud_usuario.delete_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"detail": "Usuario eliminado correctamente"}

# ===========================================================
# 📦 SOLICITUDES
# ===========================================================

@router.post("/solicitudes", response_model=schemas_solicitud.SolicitudOut)
def crear_solicitud(solicitud: schemas_solicitud.SolicitudCreate, db: Session = Depends(get_db)):
    return crud_solicitud.create_solicitud(db, solicitud)

@router.get("/solicitudes", response_model=list[schemas_solicitud.SolicitudOut])
def listar_solicitudes(db: Session = Depends(get_db)):
    return crud_solicitud.get_solicitudes(db)

@router.get("/solicitudes/{solicitud_id}", response_model=schemas_solicitud.SolicitudOut)
def obtener_solicitud(solicitud_id: int, db: Session = Depends(get_db)):
    solicitud = crud_solicitud.get_solicitud(db, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return solicitud

@router.put("/solicitudes/{solicitud_id}", response_model=schemas_solicitud.SolicitudOut)
def actualizar_solicitud(solicitud_id: int, nuevos_datos: dict, db: Session = Depends(get_db)):
    solicitud = crud_solicitud.update_solicitud(db, solicitud_id, nuevos_datos)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return solicitud

@router.delete("/solicitudes/{solicitud_id}")
def eliminar_solicitud(solicitud_id: int, db: Session = Depends(get_db)):
    solicitud = crud_solicitud.delete_solicitud(db, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"detail": "Solicitud eliminada correctamente"}

# ===========================================================
# 🧾 SERVICIOS
# ===========================================================

@router.post("/servicios")
def crear_servicio(servicio_data: dict, db: Session = Depends(get_db)):
    return crud_servicio.create_servicio(db, servicio_data)

@router.get("/servicios")
def listar_servicios(db: Session = Depends(get_db)):
    return crud_servicio.get_servicios(db)

@router.get("/servicios/{servicio_id}")
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = crud_servicio.get_servicio(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio

@router.put("/servicios/{servicio_id}")
def actualizar_servicio(servicio_id: int, nuevos_datos: dict, db: Session = Depends(get_db)):
    servicio = crud_servicio.update_servicio(db, servicio_id, nuevos_datos)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio

@router.delete("/servicios/{servicio_id}")
def eliminar_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = crud_servicio.delete_servicio(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return {"detail": "Servicio eliminado correctamente"}

# ===========================================================
# 📸 EVIDENCIAS
# ===========================================================

@router.post("/evidencias")
def crear_evidencia(evidencia_data: dict, db: Session = Depends(get_db)):
    return crud_evidencia.create_evidencia(db, evidencia_data)

@router.get("/evidencias")
def listar_evidencias(db: Session = Depends(get_db)):
    return crud_evidencia.get_evidencias(db)

@router.delete("/evidencias/{evidencia_id}")
def eliminar_evidencia(evidencia_id: int, db: Session = Depends(get_db)):
    evidencia = crud_evidencia.delete_evidencia(db, evidencia_id)
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    return {"detail": "Evidencia eliminada correctamente"}

# ===========================================================
# 💰 WALLETS
# ===========================================================

@router.post("/wallets/{usuario_id}")
def crear_wallet(usuario_id: int, db: Session = Depends(get_db)):
    return crud_wallet.create_wallet(db, usuario_id)

@router.get("/wallets/{usuario_id}")
def obtener_wallet(usuario_id: int, db: Session = Depends(get_db)):
    wallet = crud_wallet.get_wallet(db, usuario_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrada")
    return wallet

@router.put("/wallets/{usuario_id}/add")
def agregar_puntos(usuario_id: int, puntos: float, db: Session = Depends(get_db)):
    wallet = crud_wallet.update_wallet(db, usuario_id, puntos)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrada")
    return {"detail": f"Se agregaron {puntos} puntos al usuario {usuario_id}"}

@router.delete("/wallets/{usuario_id}")
def eliminar_wallet(usuario_id: int, db: Session = Depends(get_db)):
    wallet = crud_wallet.delete_wallet(db, usuario_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrada")
    return {"detail": "Wallet eliminada correctamente"}

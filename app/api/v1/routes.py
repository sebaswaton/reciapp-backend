import datetime
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas import user as schemas_user, solicitud as schemas_solicitud
from app.crud import crud_usuario, crud_solicitud, crud_servicio, crud_evidencia, crud_wallet
from app.services.business_logic import asignar_servicio, registrar_evidencia_y_puntuar
from app.api.v1.dependencies import get_current_user, require_role
from app.models.user import Usuario
from app.models.wallet import Wallet  # NUEVO
from app.services.notifications import notify_points_added, notify_service_assigned
from app.services.dashboard import get_dashboard_data
from app.crud import crud_reward, crud_wallet
from app.schemas.reward import RewardCreate, RewardOut
from fastapi.responses import StreamingResponse
from app.services.analytics import get_resumen_general, get_resumen_por_tipo, export_resumen_csv
from app.api.v1.dependencies import get_current_user



router = APIRouter()

# ===========================================================
# 🧱 DEPENDENCIA DE BASE DE DATOS
# ===========================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===========================================================
# 🧍‍♂️ USUARIOS
# ===========================================================

# 👤 Solo ADMIN puede crear usuarios manualmente
@router.post("/usuarios", response_model=schemas_user.UsuarioOut)
def crear_usuario(usuario: schemas_user.UsuarioCreate, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    db_usuario = crud_usuario.get_usuario_by_correo(db, usuario.correo)
    if db_usuario:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return crud_usuario.create_usuario(db, usuario)

# 🔒 Solo ADMIN puede listar todos los usuarios
@router.get("/usuarios", response_model=list[schemas_user.UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    return crud_usuario.get_usuarios(db)

# 👤 Usuario autenticado puede ver su propio perfil
@router.get("/usuarios/me", response_model=schemas_user.UsuarioOut)
def obtener_perfil(current_user: Usuario = Depends(get_current_user)):
    return current_user

# 🔎 Obtener usuario (solo admin)
@router.get("/usuarios/{usuario_id}", response_model=schemas_user.UsuarioOut)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    usuario = crud_usuario.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# ✏️ Actualizar usuario (admin o el propio usuario)
@router.put("/usuarios/{usuario_id}", response_model=schemas_user.UsuarioOut)
def actualizar_usuario(usuario_id: int, usuario_data: dict, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    usuario = crud_usuario.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if current_user.rol != "admin" and current_user.id != usuario.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar este usuario")

    return crud_usuario.update_usuario(db, usuario_id, usuario_data)

# 🗑️ Solo ADMIN puede eliminar usuarios
@router.delete("/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    usuario = crud_usuario.delete_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"detail": "Usuario eliminado correctamente"}

# ===========================================================
# 📦 SOLICITUDES
# ===========================================================

# Ciudadanos pueden crear solicitudes
@router.post("/solicitudes", response_model=schemas_solicitud.SolicitudOut)
def crear_solicitud(
    solicitud: schemas_solicitud.SolicitudCreate, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    # Agregar el usuario_id del usuario autenticado
    solicitud_dict = solicitud.dict()
    solicitud_dict['usuario_id'] = current_user.id
    solicitud_dict['fecha_solicitud'] = datetime.datetime.now()  # ✅ FIX: datetime.datetime.now()
    
    return crud_solicitud.create_solicitud(db, solicitud_dict)

# Admin o reciclador pueden listar solicitudes
@router.get("/solicitudes", response_model=list[schemas_solicitud.SolicitudOut])
def listar_solicitudes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """
    - Admin: ve todas las solicitudes
    - Reciclador: solo ve solicitudes pendientes o las que él aceptó
    - Ciudadano: solo ve sus propias solicitudes
    """
    if current_user.rol == "admin":
        return crud_solicitud.get_solicitudes(db)
    
    elif current_user.rol == "reciclador":
        # Recicladores ven: pendientes + las que ellos aceptaron
        todas = crud_solicitud.get_solicitudes(db)
        return [
            s for s in todas 
            if s.estado == "pendiente" or s.reciclador_id == current_user.id
        ]
    
    elif current_user.rol == "ciudadano":
        # Ciudadanos solo ven sus propias solicitudes
        todas = crud_solicitud.get_solicitudes(db)
        return [s for s in todas if s.usuario_id == current_user.id]
    
    return []

@router.get("/solicitudes/{solicitud_id}", response_model=schemas_solicitud.SolicitudOut)
def obtener_solicitud(solicitud_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    solicitud = crud_solicitud.get_solicitud(db, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    # Los ciudadanos solo pueden ver sus propias solicitudes
    if current_user.rol == "ciudadano" and solicitud.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes acceder a esta solicitud")

    return solicitud

@router.put("/solicitudes/{solicitud_id}", response_model=schemas_solicitud.SolicitudOut)
def actualizar_solicitud(solicitud_id: int, nuevos_datos: dict, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    solicitud = crud_solicitud.get_solicitud(db, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    # ✅ PERMITIR: Admin, dueño de la solicitud (ciudadano), o reciclador que la aceptó
    es_admin = current_user.rol == "admin"
    es_dueno = solicitud.usuario_id == current_user.id
    es_reciclador_asignado = (
        current_user.rol == "reciclador" and 
        solicitud.reciclador_id == current_user.id
    )
    
    # ✅ NUEVO: Permitir recicladores actualizar solicitudes que aceptan
    es_reciclador_actualizando_estado = (
        current_user.rol == "reciclador" and 
        "estado" in nuevos_datos and 
        nuevos_datos["estado"] in ["aceptada", "completada"]
    )

    if not (es_admin or es_dueno or es_reciclador_asignado or es_reciclador_actualizando_estado):
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar esta solicitud")

    return crud_solicitud.update_solicitud(db, solicitud_id, nuevos_datos)

@router.delete("/solicitudes/{solicitud_id}")
def eliminar_solicitud(solicitud_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    solicitud = crud_solicitud.delete_solicitud(db, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"detail": "Solicitud eliminada correctamente"}

# ===========================================================
# 🧾 SERVICIOS
# ===========================================================

@router.post("/servicios")
def crear_servicio(servicio_data: dict, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    return crud_servicio.create_servicio(db, servicio_data)

@router.get("/servicios")
def listar_servicios(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    return crud_servicio.get_servicios(db)

@router.get("/servicios/{servicio_id}")
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    servicio = crud_servicio.get_servicio(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio

@router.put("/servicios/{servicio_id}")
def actualizar_servicio(servicio_id: int, nuevos_datos: dict, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    servicio = crud_servicio.update_servicio(db, servicio_id, nuevos_datos)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio

@router.delete("/servicios/{servicio_id}")
def eliminar_servicio(servicio_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    servicio = crud_servicio.delete_servicio(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return {"detail": "Servicio eliminado correctamente"}

# ===========================================================
# 📸 EVIDENCIAS
# ===========================================================

@router.post("/evidencias")
def crear_evidencia(evidencia_data: dict, db: Session = Depends(get_db), _: Usuario = Depends(require_role("reciclador"))):
    return crud_evidencia.create_evidencia(db, evidencia_data)

@router.get("/evidencias")
def listar_evidencias(db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    return crud_evidencia.get_evidencias(db)

@router.delete("/evidencias/{evidencia_id}")
def eliminar_evidencia(evidencia_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    evidencia = crud_evidencia.delete_evidencia(db, evidencia_id)
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    return {"detail": "Evidencia eliminada correctamente"}

# ===========================================================
# 💰 WALLETS
# ===========================================================

@router.post("/wallets/{usuario_id}")
def crear_wallet(usuario_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    return crud_wallet.create_wallet(db, usuario_id)

# 🔹 IMPORTANTE: Este endpoint debe ir ANTES del GET /wallets/{usuario_id}
@router.post("/wallets/{usuario_id}/redeem/{reward_id}")
def canjear_puntos(usuario_id: int, reward_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Canjear puntos por una recompensa"""
    from app.models.reward import Reward
    
    # Verificar que existe la recompensa
    reward = crud_reward.get_reward(db, reward_id)  # ✅ Usar CRUD en lugar de query directo
    if not reward:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")
    
    # Verificar y descontar puntos
    wallet = crud_wallet.redeem_points(db, usuario_id, reward.costo_puntos)
    if wallet == "INSUFFICIENT_POINTS":
        raise HTTPException(status_code=400, detail="Puntos insuficientes para canjear esta recompensa")
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrada")

    return {
        "mensaje": f"Canje exitoso de '{reward.nombre}'",
        "puntos_restantes": wallet.puntos
    }

@router.put("/wallets/{usuario_id}/add")
def agregar_puntos(usuario_id: int, puntos: float, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    wallet = crud_wallet.update_wallet(db, usuario_id, puntos)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrada")
    return {"detail": f"Se agregaron {puntos} puntos al usuario {usuario_id}"}

@router.get("/wallets/{usuario_id}")
def obtener_wallet(usuario_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Obtener wallet de un usuario. Si no existe, crear uno nuevo."""
    wallet = db.query(Wallet).filter(Wallet.usuario_id == usuario_id).first()
    
    # Si no existe, crear uno nuevo
    if not wallet:
        wallet = Wallet(
            usuario_id=usuario_id,
            puntos=0
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    # Solo admin o el propio usuario puede verla
    if current_user.rol != "admin" and current_user.id != usuario_id:
        raise HTTPException(status_code=403, detail="No puedes acceder a esta wallet")

    return {
        "id": wallet.id,
        "usuario_id": wallet.usuario_id,
        "puntos": wallet.puntos
    }

@router.delete("/wallets/{usuario_id}")
def eliminar_wallet(usuario_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_role("admin"))):
    wallet = crud_wallet.delete_wallet(db, usuario_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrada")
    return {"detail": "Wallet eliminada correctamente"}

# ===========================================================
# 🔄 LÓGICA DE NEGOCIO
# ===========================================================

@router.post("/asignar-servicio/{solicitud_id}/{reciclador_id}")
def asignar(db: Session = Depends(get_db), solicitud_id: int = None, reciclador_id: int = None, _: Usuario = Depends(require_role("admin"))):
    return asignar_servicio(db, solicitud_id, reciclador_id)

@router.post("/registrar-evidencia/{solicitud_id}")
def registrar_evidencia(solicitud_id: int, evidencia_data: dict, db: Session = Depends(get_db), _: Usuario = Depends(require_role("reciclador"))):
    return registrar_evidencia_y_puntuar(db, solicitud_id, evidencia_data)

# ===========================================================
# 🔔 NOTIFICACIONES
# ===========================================================

@router.post("/notify/{usuario_id}")
def enviar_notificacion(usuario_id: int, mensaje: str, db: Session = Depends(get_db)):
    return notify_points_added(usuario_id, mensaje)

# ===========================================================
# 📊 DASHBOARD
# ===========================================================

@router.get("/dashboard")
def ver_dashboard(db: Session = Depends(get_db)):
    return get_dashboard_data(db)



# ===========================================================
# 🎁 RECOMPENSAS
# ===========================================================

@router.post("/rewards", response_model=RewardOut)
def crear_reward(reward: RewardCreate, db: Session = Depends(get_db)):
    return crud_reward.create_reward(db, reward)

@router.get("/rewards", response_model=list[RewardOut])
def listar_rewards(db: Session = Depends(get_db)):
    return crud_reward.get_rewards(db)

@router.delete("/rewards/{reward_id}")
def eliminar_reward(reward_id: int, db: Session = Depends(get_db)):
    reward = crud_reward.delete_reward(db, reward_id)
    if not reward:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")
    return {"detail": "Recompensa eliminada correctamente"}

# ===========================================================
# 📊 ANALYTICS
# ===========================================================

@router.get("/analytics/resumen")
def resumen_general(db: Session = Depends(get_db)):
    return get_resumen_general(db)

@router.get("/analytics/por-tipo")
def resumen_por_tipo(db: Session = Depends(get_db)):
    return get_resumen_por_tipo(db)

@router.get("/analytics/export")
def exportar_csv(db: Session = Depends(get_db)):
    csv_data = export_resumen_csv(db)
    return StreamingResponse(
        StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reportes_reciclaje.csv"}
    )
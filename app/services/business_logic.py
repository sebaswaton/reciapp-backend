from sqlalchemy.orm import Session
from app.models.solicitud import Solicitud
from app.models.servicio import Servicio
from app.models.evidencia import Evidencia
from app.models.wallet import Wallet
from app.crud import crud_wallet

# Tabla de equivalencias: puntos por kg de material
PUNTOS_MATERIAL = {
    "plastico": 5,
    "carton": 3,
    "vidrio": 4,
    "metal": 6
}

def asignar_servicio(db: Session, solicitud_id: int, reciclador_id: int):
    """Asigna una solicitud a un reciclador creando un servicio."""
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        return {"error": "Solicitud no encontrada"}
    servicio = Servicio(solicitud_id=solicitud_id, reciclador_id=reciclador_id, estado="en proceso")
    solicitud.estado = "asignado"
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio


def registrar_evidencia_y_puntuar(db: Session, solicitud_id: int, datos_evidencia: dict):
    """Guarda evidencia y otorga puntos al reciclador según el material recolectado."""
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        return {"error": "Solicitud no encontrada"}

    evidencia = Evidencia(
        solicitud_id=solicitud_id,
        imagen_url=datos_evidencia["imagen_url"],
        material=datos_evidencia["material"],
        peso_kg=datos_evidencia["peso_kg"]
    )
    db.add(evidencia)

    # Calcular puntos
    puntos = PUNTOS_MATERIAL.get(evidencia.material.lower(), 1) * evidencia.peso_kg

    # Actualizar wallet del reciclador
    servicio = db.query(Servicio).filter(Servicio.solicitud_id == solicitud_id).first()
    wallet = crud_wallet.get_wallet(db, servicio.reciclador_id)
    if wallet:
        crud_wallet.update_wallet(db, servicio.reciclador_id, puntos)
    else:
        crud_wallet.create_wallet(db, servicio.reciclador_id)
        crud_wallet.update_wallet(db, servicio.reciclador_id, puntos)

    # Cambiar estado de solicitud
    solicitud.estado = "completada"
    db.commit()
    db.refresh(solicitud)

    return {"mensaje": "Evidencia registrada y puntos asignados", "puntos_otorgados": puntos}

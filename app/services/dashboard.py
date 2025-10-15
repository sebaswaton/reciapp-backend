from sqlalchemy.orm import Session
from app.models.user import Usuario
from app.models.solicitud import Solicitud
from app.models.wallet import Wallet

def get_dashboard_data(db: Session):
    total_usuarios = db.query(Usuario).count()
    total_solicitudes = db.query(Solicitud).count()
    total_wallets = db.query(Wallet).count()

    total_puntos = sum([w.puntos for w in db.query(Wallet).all()])
    solicitudes_completadas = db.query(Solicitud).filter_by(estado="completado").count()

    top_usuarios = db.query(Wallet).order_by(Wallet.puntos.desc()).limit(5).all()

    return {
        "total_usuarios": total_usuarios,
        "total_solicitudes": total_solicitudes,
        "solicitudes_completadas": solicitudes_completadas,
        "total_puntos": total_puntos,
        "top_usuarios": [
            {"usuario_id": u.usuario_id, "puntos": u.puntos} for u in top_usuarios
        ],
    }

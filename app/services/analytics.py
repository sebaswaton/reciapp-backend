from sqlalchemy.orm import Session
from app.models.solicitud import Solicitud
from app.models.wallet import Wallet
from datetime import datetime
import csv
from io import StringIO

def get_resumen_general(db: Session):
    total_solicitudes = db.query(Solicitud).count()
    completadas = db.query(Solicitud).filter_by(estado="completado").count()
    pendientes = db.query(Solicitud).filter_by(estado="pendiente").count()

    total_puntos = sum([w.puntos for w in db.query(Wallet).all()])
    promedio_puntos = total_puntos / db.query(Wallet).count() if db.query(Wallet).count() > 0 else 0

    return {
        "total_solicitudes": total_solicitudes,
        "completadas": completadas,
        "pendientes": pendientes,
        "total_puntos": total_puntos,
        "promedio_puntos": promedio_puntos
    }

def get_resumen_por_tipo(db: Session):
    tipos = db.query(Solicitud.tipo_residuo).distinct()
    resumen = []
    for tipo in tipos:
        total_tipo = db.query(Solicitud).filter(Solicitud.tipo_residuo == tipo[0]).count()
        completadas = db.query(Solicitud).filter(Solicitud.tipo_residuo == tipo[0], Solicitud.estado == "completado").count()
        resumen.append({
            "tipo_residuo": tipo[0],
            "total": total_tipo,
            "completadas": completadas
        })
    return resumen

def export_resumen_csv(db: Session):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tipo de Residuo", "Total", "Completadas"])
    for r in get_resumen_por_tipo(db):
        writer.writerow([r["tipo_residuo"], r["total"], r["completadas"]])
    output.seek(0)
    return output.getvalue()

# app/services/notifications.py
from fastapi import HTTPException

# Simulación básica de envío de notificación
def send_notification(usuario_id: int, mensaje: str):
    # Aquí podrías integrar Twilio, SendGrid o Firebase en el futuro
    print(f"🔔 Notificación enviada al usuario {usuario_id}: {mensaje}")
    return {"usuario_id": usuario_id, "mensaje": mensaje}

# Notificar al usuario cuando gana puntos
def notify_points_added(usuario_id: int, puntos: float):
    mensaje = f"Has recibido {puntos} puntos por tu reciclaje. ¡Sigue ayudando al planeta! 🌱"
    return send_notification(usuario_id, mensaje)

# Notificar al reciclador cuando se le asigna un nuevo servicio
def notify_service_assigned(reciclador_id: int, solicitud_id: int):
    mensaje = f"Tienes una nueva solicitud asignada (ID: {solicitud_id}). 🚛"
    return send_notification(reciclador_id, mensaje)

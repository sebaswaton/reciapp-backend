from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import Usuario
from app.models.solicitud import Solicitud

router = APIRouter()

# Almacenar conexiones activas
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.recicladores_disponibles: Dict[int, dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.recicladores_disponibles:
            del self.recicladores_disponibles[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))
    
    async def notify_nearby_recyclers(self, solicitud: dict, radio_km: float = 5.0):
        """Notificar a recicladores cercanos"""
        for reciclador_id, reciclador_data in self.recicladores_disponibles.items():
            # Aquí calcularías la distancia (simplificado)
            await self.send_personal_message({
                "type": "nueva_solicitud",
                "solicitud": solicitud
            }, reciclador_id)
    
    def update_recycler_location(self, user_id: int, lat: float, lng: float):
        """Actualizar ubicación del reciclador"""
        self.recicladores_disponibles[user_id] = {
            "lat": lat,
            "lng": lng,
            "timestamp": datetime.now().isoformat()
        }
    
    async def broadcast_location(self, solicitud_id: int, reciclador_id: int, lat: float, lng: float):
        """Transmitir ubicación del reciclador al usuario que hizo la solicitud"""
        # Obtener el usuario de la solicitud
        db = SessionLocal()
        solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
        if solicitud:
            await self.send_personal_message({
                "type": "ubicacion_reciclador",
                "solicitud_id": solicitud_id,
                "lat": lat,
                "lng": lng
            }, solicitud.usuario_id)
        db.close()

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "ubicacion_reciclador":
                # Actualizar ubicación del reciclador
                manager.update_recycler_location(
                    user_id, 
                    message["lat"], 
                    message["lng"]
                )
                
                # Si está en servicio, transmitir al usuario
                if "solicitud_id" in message:
                    await manager.broadcast_location(
                        message["solicitud_id"],
                        user_id,
                        message["lat"],
                        message["lng"]
                    )
            
            elif message["type"] == "nueva_solicitud":
                # Notificar a recicladores cercanos
                await manager.notify_nearby_recyclers(message["solicitud"])
            
            elif message["type"] == "aceptar_solicitud":
                # Notificar al usuario que su solicitud fue aceptada
                solicitud_id = message["solicitud_id"]
                db = SessionLocal()
                solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
                if solicitud:
                    await manager.send_personal_message({
                        "type": "solicitud_aceptada",
                        "solicitud_id": solicitud_id,
                        "reciclador_id": user_id
                    }, solicitud.usuario_id)
                db.close()
            
            elif message["type"] == "rechazar_solicitud":
                # Log del rechazo
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
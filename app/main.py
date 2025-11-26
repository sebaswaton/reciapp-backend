import os
import json
import time
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Importaciones de modelos y base de datos
from app.models.base import Base
from app.db.session import engine
from app import models  # Importa todo para registrar las clases
from app.models import user, solicitud, servicio, evidencia, wallet

# Importaciones de rutas
from app.api.v1 import routes
from app.api.v1 import routes_auth
from app.api.v1.routes import router as api_router

# Crear la aplicación FastAPI
app = FastAPI()
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

# Configurar CORS para FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if FRONTEND_URL == "*" else [FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# GESTOR DE CONEXIONES WEBSOCKET
# ============================================
class ConnectionManager:
    def __init__(self):
        # Diccionario: user_id -> Set de WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Diccionario para saber qué tipo de usuario es (ciudadano/reciclador)
        self.user_types: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str, user_type: str = "ciudadano"):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.user_types[user_id] = user_type
        print(f"✅ Usuario {user_id} ({user_type}) conectado. Total: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_types:
                    del self.user_types[user_id]
        print(f"❌ Usuario {user_id} desconectado")

    async def send_personal_message(self, message: dict, user_id: str):
        """Enviar mensaje a un usuario específico (todas sus conexiones)"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error enviando mensaje a {user_id}: {e}")
                    disconnected.append(connection)
            
            # Limpiar conexiones muertas
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast_to_recicladores(self, message: dict):
        """Enviar mensaje a todos los recicladores conectados"""
        print(f"📢 Broadcasting a recicladores: {message.get('type')}")
        count = 0
        for user_id, connections in list(self.active_connections.items()):
            if self.user_types.get(user_id) == "reciclador":
                disconnected = []
                for connection in connections:
                    try:
                        await connection.send_text(json.dumps(message))
                        count += 1
                    except Exception as e:
                        print(f"Error broadcasting a reciclador {user_id}: {e}")
                        disconnected.append(connection)
                
                # Limpiar conexiones muertas
                for conn in disconnected:
                    self.disconnect(conn, user_id)
        print(f"✅ Mensaje enviado a {count} recicladores")

    async def broadcast_to_all(self, message: dict):
        """Enviar mensaje a todos los usuarios conectados"""
        for user_id, connections in list(self.active_connections.items()):
            disconnected = []
            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error broadcasting: {e}")
                    disconnected.append(connection)
            
            # Limpiar conexiones muertas
            for conn in disconnected:
                self.disconnect(conn, user_id)

# Instancia global del gestor de conexiones
manager = ConnectionManager()

# ============================================
# WEBSOCKET ENDPOINT
# ============================================
@app.websocket("/realtime/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint para conexión en tiempo real.
    URL: ws://localhost:8000/realtime/ws/{user_id}?type=ciudadano
    Query params: type = "ciudadano" | "reciclador"
    """
    # Obtener tipo de usuario desde query params
    user_type = websocket.query_params.get("type", "ciudadano")
    
    await manager.connect(websocket, user_id, user_type)
    
    try:
        while True:
            # Recibir mensajes del cliente
            text_data = await websocket.receive_text()
            data = json.loads(text_data)
            event_type = data.get("type")
            
            print(f"📨 [{user_type.upper()}] {user_id}: {event_type}")
            
            # =============== CIUDADANO CREA SOLICITUD ===============
            if event_type == "nueva_solicitud":
                solicitud = data.get("solicitud")
                
                # Broadcast a todos los recicladores
                await manager.broadcast_to_recicladores({
                    "type": "nueva_solicitud",
                    "solicitud": solicitud
                })
                
                print(f"✅ Solicitud {solicitud.get('id')} notificada a recicladores")
            
            # =============== ACTUALIZAR DASHBOARD CIUDADANO ===============
            elif event_type == "solicitud_creada":
                solicitud = data.get("solicitud")
                ciudadano_id = str(data.get("ciudadano_id"))
                
                await manager.send_personal_message({
                    "type": "solicitud_creada",
                    "solicitud": solicitud
                }, ciudadano_id)
                
                print(f"✅ Dashboard ciudadano {ciudadano_id} actualizado")
            
            # =============== RECICLADOR ACEPTA SOLICITUD ===============
            elif event_type == "aceptar_solicitud":
                solicitud_id = data.get("solicitud_id")
                ciudadano_id = str(data.get("ciudadano_id"))
                
                # Notificar al ciudadano que su solicitud fue aceptada
                await manager.send_personal_message({
                    "type": "solicitud_aceptada",
                    "solicitud_id": solicitud_id,
                    "reciclador_id": user_id
                }, ciudadano_id)
                
                # Actualizar dashboard del ciudadano
                await manager.send_personal_message({
                    "type": "solicitud_actualizada",
                    "solicitud_id": solicitud_id,
                    "estado": "aceptada"
                }, ciudadano_id)
                
                print(f"✅ Solicitud {solicitud_id} aceptada por reciclador {user_id}")
            
            # =============== UBICACIÓN RECICLADOR EN TIEMPO REAL ===============
            elif event_type == "ubicacion_reciclador":
                ciudadano_id = data.get("ciudadano_id")
                solicitud_id = data.get("solicitud_id")
                lat = data.get("lat")
                lng = data.get("lng")
                
                if ciudadano_id:
                    await manager.send_personal_message({
                        "type": "ubicacion_reciclador",
                        "lat": lat,
                        "lng": lng,
                        "solicitud_id": solicitud_id
                    }, str(ciudadano_id))
            
            # =============== COMPLETAR SOLICITUD ===============
            elif event_type == "completar_solicitud":
                solicitud_id = data.get("solicitud_id")
                ciudadano_id = str(data.get("ciudadano_id"))
                
                # Notificar al ciudadano
                await manager.send_personal_message({
                    "type": "solicitud_completada",
                    "solicitud_id": solicitud_id
                }, ciudadano_id)
                
                # Actualizar dashboard del ciudadano
                await manager.send_personal_message({
                    "type": "solicitud_actualizada",
                    "solicitud_id": solicitud_id,
                    "estado": "completada"
                }, ciudadano_id)
                
                print(f"✅ Solicitud {solicitud_id} completada")
            
            # =============== RECHAZAR SOLICITUD ===============
            elif event_type == "rechazar_solicitud":
                solicitud_id = data.get("solicitud_id")
                print(f"⚠️ Solicitud {solicitud_id} rechazada por reciclador {user_id}")
            
            # =============== PING/PONG PARA MANTENER CONEXIÓN VIVA ===============
            elif event_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"🔌 Usuario {user_id} desconectado normalmente")
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON de {user_id}: {e}")
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"❌ Error en WebSocket {user_id}: {e}")
        manager.disconnect(websocket, user_id)

# ============================================
# ENDPOINTS HTTP PARA NOTIFICACIONES
# ============================================
@app.post("/api/notify/solicitud_creada")
async def notify_solicitud_creada(data: dict):
    """
    Endpoint HTTP para notificar desde otras partes del backend
    cuando se crea una solicitud.
    """
    solicitud = data.get("solicitud")
    ciudadano_id = str(data.get("ciudadano_id"))
    
    # Notificar al ciudadano
    await manager.send_personal_message({
        "type": "solicitud_creada",
        "solicitud": solicitud
    }, ciudadano_id)
    
    # Notificar a todos los recicladores
    await manager.broadcast_to_recicladores({
        "type": "nueva_solicitud",
        "solicitud": solicitud
    })
    
    print(f"✅ Notificación HTTP: solicitud {solicitud.get('id')} creada")
    return {"status": "notified"}

@app.post("/api/notify/solicitud_actualizada")
async def notify_solicitud_actualizada(data: dict):
    """
    Endpoint HTTP para notificar cuando se actualiza una solicitud.
    """
    solicitud_id = data.get("solicitud_id")
    ciudadano_id = str(data.get("ciudadano_id"))
    estado = data.get("estado")
    
    await manager.send_personal_message({
        "type": "solicitud_actualizada",
        "solicitud_id": solicitud_id,
        "estado": estado
    }, ciudadano_id)
    
    print(f"✅ Notificación HTTP: solicitud {solicitud_id} actualizada a {estado}")
    return {"status": "notified"}

# ============================================
# STARTUP EVENT
# ============================================
@app.on_event("startup")
async def startup_event():
    """Crear tablas de base de datos con reintentos"""
    max_retries = 30
    retry_interval = 2  # segundos
    
    for attempt in range(max_retries):
        try:
            # Obtener la URL de conexión de forma segura
            db_url = str(engine.url)
            # Ocultar la contraseña en los logs
            if '@' in db_url:
                safe_url = db_url.split('@')[1]
                print(f"✅ Conectando a: {safe_url}")
            
            # Intentar crear las tablas
            Base.metadata.create_all(bind=engine)
            print("✅ Tablas creadas exitosamente")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⏳ Esperando a la base de datos... intento {attempt + 1}/{max_retries}")
                print(f"   Error: {str(e)}")
                time.sleep(retry_interval)
            else:
                print(f"❌ No se pudo conectar a la base de datos después de {max_retries} intentos")
                print(f"   Error final: {str(e)}")
                raise

# ============================================
# HEALTHCHECK
# ============================================
@app.get("/healthcheck")
def healthcheck():
    return {
        "status": "ok",
        "websocket_connections": len(manager.active_connections),
        "recicladores_online": sum(
            1 for user_type in manager.user_types.values() 
            if user_type == "reciclador"
        )
    }

# ============================================
# INCLUIR ROUTERS
# ============================================
app.include_router(routes_auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(routes.router, prefix="/api", tags=["Usuarios y Recursos"])
app.include_router(api_router)
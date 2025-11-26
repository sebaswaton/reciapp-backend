import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import time

# Importaciones de modelos y base de datos
from app.models.base import Base
from app.db.session import engine
from app import models  # Importa todo para registrar las clases
from app.models import user, solicitud, servicio, evidencia, wallet

# Importaciones de rutas
from app.api.v1 import routes
from app.api.v1 import routes_auth
from app.api.v1.routes import router as api_router
from app.services import realtime

# Crear la aplicación FastAPI
app = FastAPI()

# Configurar orígenes permitidos para CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

# Lista de orígenes permitidos
if FRONTEND_URL:
    allowed_origins = [
        "http://localhost:5173",  # Vite desarrollo
        "http://localhost:3000",  # React desarrollo
        FRONTEND_URL,  # Producción (Netlify)
    ]
else:
    # Si no hay FRONTEND_URL configurado, permite todos (solo para desarrollo)
    allowed_origins = ["*"]

# Crear servidor Socket.IO con configuración corregida
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=allowed_origins if allowed_origins != ["*"] else "*",
    logger=True,
    engineio_logger=True,
    cors_credentials=True,
)

# Configurar CORS para FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Evento de startup para crear tablas con reintentos
@app.on_event("startup")
async def startup_event():
    max_retries = 30
    retry_interval = 2  # segundos
    
    print(f"🔗 Configuración de aplicación:")
    print(f"   📍 Orígenes CORS permitidos: {allowed_origins}")
    print(f"   🌐 FRONTEND_URL: {FRONTEND_URL or 'No configurado (permitiendo todos)'}")
    
    for attempt in range(max_retries):
        try:
            # Obtener info de la conexión de BD
            from app.db.session import SessionLocal
            db = SessionLocal()
            
            # Mostrar info de conexión (ocultar contraseña)
            db_url = str(engine.url)
            if '@' in db_url:
                parts = db_url.split('@')
                host_part = parts[1] if len(parts) > 1 else 'unknown'
                print(f"   🗄️  Conectando a: {host_part}")
            
            # Intentar crear las tablas
            Base.metadata.create_all(bind=engine)
            print("   ✅ Tablas creadas exitosamente")
            db.close()
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

# Healthcheck
@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "ReciApp API - Backend funcionando correctamente",
        "docs": "/docs",
        "status": "online",
        "websocket": "/ws"
    }

# Incluir routers
app.include_router(routes_auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(routes.router, prefix="/api", tags=["Usuarios y Recursos"])
app.include_router(api_router)
app.include_router(realtime.router, prefix="/realtime", tags=["Real Time"])

# Event handlers de Socket.IO con logging mejorado
@sio.event
async def connect(sid, environ):
    # Obtener el origen de la conexión
    origin = environ.get('HTTP_ORIGIN', 'Unknown')
    user_agent = environ.get('HTTP_USER_AGENT', 'Unknown')
    print(f"✅ Cliente conectado: {sid}")
    print(f"   📍 Origen: {origin}")
    print(f"   🖥️  User-Agent: {user_agent[:50]}...")
    
    # Enviar confirmación al cliente
    await sio.emit('connection_status', {
        'status': 'connected', 
        'sid': sid,
        'message': 'Conexión establecida exitosamente'
    }, room=sid)

@sio.event
async def disconnect(sid):
    print(f"❌ Cliente desconectado: {sid}")

@sio.event
async def mensaje(sid, data):
    print(f"📨 Mensaje recibido de {sid}: {data}")
    await sio.emit('respuesta', {'mensaje': 'Recibido', 'data': data}, room=sid)

@sio.event
async def error(sid, data):
    print(f"⚠️ Error de Socket.IO para {sid}: {data}")

# Envolver la app de FastAPI con Socket.IO
socket_app = socketio.ASGIApp(
    sio,
    app,
    socketio_path='/ws'  # Esto hace que Socket.IO escuche en /ws/*
)
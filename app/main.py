from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

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

# Crear servidor Socket.IO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=    "https://enchanting-biscochitos-af791d.netlify.app",
     # En producción, especifica tus dominios
    logger=True,
    engineio_logger=True
)

# Configurar CORS para FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción, limita esto a tu dominio específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck
@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

# Incluir routers
app.include_router(routes_auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(routes.router, prefix="/api", tags=["Usuarios y Recursos"])
app.include_router(api_router)
app.include_router(realtime.router, prefix="/realtime", tags=["Real Time"])

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Event handlers de Socket.IO
@sio.event
async def connect(sid, environ):
    print(f"Cliente conectado: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Cliente desconectado: {sid}")

@sio.event
async def mensaje(sid, data):
    print(f"Mensaje recibido de {sid}: {data}")
    await sio.emit('respuesta', {'mensaje': 'Recibido'}, room=sid)

# Envolver la app de FastAPI con Socket.IO
socket_app = socketio.ASGIApp(
    sio,
    app,
    socketio_path='/ws'  # Esto hace que Socket.IO escuche en /ws/*
)
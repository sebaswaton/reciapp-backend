from fastapi import FastAPI
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

# Crear la aplicación
app = FastAPI()

# ← CORS DEBE IR AQUÍ, JUSTO DESPUÉS DE CREAR app
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
#app.include_router(routes.router, prefix="", tags=["Endpoints"])
app.include_router(api_router)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)
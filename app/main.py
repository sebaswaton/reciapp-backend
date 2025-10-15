from fastapi import FastAPI

app = FastAPI()

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

from app.models.base import Base
from app.db.session import engine
from app import models  # Importa todo para registrar las clases
from app.models import user, solicitud, servicio, evidencia, wallet
from app.api.v1 import routes_auth

app.include_router(routes_auth.router, prefix="/auth", tags=["Autenticación"])


Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as api_router

# CORS para permitir conexión desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción, limita esto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


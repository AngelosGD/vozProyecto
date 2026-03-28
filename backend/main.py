from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from database import init_db

app = FastAPI(title="Sistema de Seguridad por Voz")

# Permitir que el frontend se conecte (cualquier origen por ahora)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar la base de datos al arrancar
init_db()

# Registrar rutas
app.include_router(auth_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "API de reconocimiento de voz activa ✅"}
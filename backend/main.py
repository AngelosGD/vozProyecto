from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from database import init_db

app = FastAPI(title="Sistema de Seguridad por Voz")

# Permite que el frontend se conecte 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar la base de datos al iniciar la aplicación
init_db()

# Registrar rutas
app.include_router(auth_router, prefix="/api")


@app.get("/") #Ruta por defecto para verificar que la API está activa
def root():
    return {"message": "API de reconocimiento de voz activa"}
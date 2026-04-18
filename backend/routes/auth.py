from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from database import get_client
from utils.audio import save_temp_audio, delete_temp_audio
from model.recognizer import register_voice, login_voice, delete_voice
 
router = APIRouter()
 
 
#  POST /api/usuarios 
@router.post("/usuarios")
async def crear_usuario(
    nombre: str = Form(...),
    audio: UploadFile = File(...)
):
    """
    Registra un nuevo usuario con su voz.
    Recibe: nombre (texto) + audio .wav (archivo)
    """
    nombre = nombre.strip().lower()
    client = get_client()
 
    # 1. Verificar que el usuario no exista ya en Supabase
    existe = client.table("usuarios").select("id").eq("nombre", nombre).execute()
    if existe.data:
        raise HTTPException(status_code=400, detail=f"El usuario '{nombre}' ya existe")
 
    # 2. Guardar el audio temporalmente
    audio_path = await save_temp_audio(audio, nombre)
 
    # 3. Registrar la voz con el módulo de IA 
    resultado = register_voice(nombre, str(audio_path))
 
    # 4. Limpiar el audio temporal
    delete_temp_audio(audio_path)
 
    if not resultado["success"]:
        raise HTTPException(status_code=500, detail=resultado["message"])
 
    # 5. Insertar usuario en Supabase
    client.table("usuarios").insert({"nombre": nombre}).execute()
 
    return {"success": True, "message": f"Usuario '{nombre}' registrado correctamente"}
 
 
#  POST /api/login-voz 
@router.post("/login-voz")
async def login_con_voz(audio: UploadFile = File(...)):
    """
    Verifica si la voz en el audio corresponde a un usuario registrado.
    Recibe: audio .wav (archivo)
    Retorna: si se permite o deniega el acceso
    """
    client = get_client()
 
    # 1. Guardar audio temporal
    audio_path = await save_temp_audio(audio, "login_temp")
 
    # 2. Comparar con voces registradas (Integrante 2)
    resultado = login_voice(str(audio_path))
 
    # 3. Limpiar audio temporal
    delete_temp_audio(audio_path)
 
    # 4. Verificar que el usuario encontrado esté activo en Supabase
    if resultado["success"] and resultado.get("match"):
        user = client.table("usuarios") \
            .select("activo") \
            .eq("nombre", resultado["match"]) \
            .execute()
 
        if not user.data or user.data[0]["activo"] is False:
            resultado["success"] = False
            resultado["message"] = "Usuario desactivado o no encontrado en BD"
 
    # 5. Guardar log del intento (siempre, pase o no)
    client.table("logs_acceso").insert({
        "nombre":    resultado.get("match") or "desconocido",
        "resultado": "permitido" if resultado["success"] else "denegado",
        "confianza": resultado.get("confidence")
    }).execute()
 
    return resultado
 
 
# GET /api/usuarios 
@router.get("/usuarios")
def obtener_usuarios():
    """Lista todos los usuarios registrados."""
    client = get_client()
    response = client.table("usuarios") \
        .select("id, nombre, activo, creado_en") \
        .execute()
    return response.data
 
 
#  GET /api/usuarios/{nombre} 
@router.get("/usuarios/{nombre}")
def obtener_usuario(nombre: str):
    """Obtiene info de un usuario específico."""
    client = get_client()
    response = client.table("usuarios") \
        .select("id, nombre, activo, creado_en") \
        .eq("nombre", nombre.lower()) \
        .execute()
 
    if not response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
 
    return response.data[0]
 
 
#  DELETE /api/usuarios/{nombre} 
@router.delete("/usuarios/{nombre}")
def eliminar_usuario(nombre: str):
    """Elimina un usuario de Supabase y su voz registrada."""
    nombre = nombre.lower()
    client = get_client()
 
    # Eliminar voz del módulo de IA
    delete_voice(nombre)
 
    # Eliminar de Supabase
    response = client.table("usuarios").delete().eq("nombre", nombre).execute()
 
    if not response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en BD")
 
    return {"success": True, "message": f"Usuario '{nombre}' eliminado"}
 
 
#  GET /api/logs 
@router.get("/logs")
def obtener_logs():
    """Retorna el historial de intentos de acceso."""
    client = get_client()
    response = client.table("logs_acceso") \
        .select("*") \
        .order("fecha", desc=True) \
        .limit(50) \
        .execute()
    return response.data
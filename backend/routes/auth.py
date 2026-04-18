from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from database import get_connection
from utils.audio import save_temp_audio, delete_temp_audio
from model.recognizer import register_voice, login_voice, delete_voice

router = APIRouter()
 
 
# ─── POST /api/usuarios ───────────────────────────────────────────────────────
@router.post("/usuarios")
async def crear_usuario(
    nombre: str = Form(...), #Recibe un nombre de un formulario
    audio: UploadFile = File(...) #Recibir un archivo de audio
):
    nombre = nombre.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()

    #Verificar que no exista el usuario
    cursor.execute("SELECT id FROM usuarios WHERE nombre = %s", (nombre,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail=f"El usuario '{nombre}' ya existe") #Verifica que el usuario no exista antes de registrarlo 

    #Guardar audio temporal
    audio_path = await save_temp_audio(audio, nombre)

    #Registrar voz con IA
    resultado = register_voice(nombre, str(audio_path))

    #Limpiar audio temporal
    delete_temp_audio(audio_path)

    if not resultado["success"]:
        conn.close()
        raise HTTPException(status_code=500, detail=resultado["message"])

    #Insertar usuario en PostgreSQL
    cursor.execute("INSERT INTO usuarios (nombre) VALUES (%s)", (nombre,))
    conn.commit()
    conn.close()

    return {"success": True, "message": f"Usuario '{nombre}' registrado correctamente"}
 
 
# ─── POST /api/login-voz ──────────────────────────────────────────────────────
@router.post("/login-voz")
async def login_con_voz(audio: UploadFile = File(...)):
    conn = get_connection()
    cursor = conn.cursor()

    #Guardar audio temporal
    audio_path = await save_temp_audio(audio, "login_temp")

    #Comparar voz
    resultado = login_voice(str(audio_path))

    #Limpiar audio
    delete_temp_audio(audio_path)

    #Verificar que el usuario esté activo en PostgreSQL
    if resultado["success"] and resultado.get("match"):#Si se encontró una coincidencia, verificar que el usuario esta activo
        cursor.execute(
            "SELECT activo FROM usuarios WHERE nombre = %s",
            (resultado["match"],)
        )
        user = cursor.fetchone()

        if not user or not user["activo"]: #Si el usuario no existe o no está activo no entra
            resultado["success"] = False
            resultado["message"] = "Usuario desactivado o no encontrado en BD"

    #Guardar inicio de sesion
    cursor.execute(
        "INSERT INTO logs_acceso (nombre, resultado, confianza) VALUES (%s, %s, %s)",
        (
            resultado.get("match") or "desconocido",
            "permitido" if resultado["success"] else "denegado",
            resultado.get("confidence")
        )
    )
    conn.commit()
    conn.close()

    return resultado
 
 
# ─── GET /api/usuarios ────────────────────────────────────────────────────────
@router.get("/usuarios")
def obtener_usuarios():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre, activo, creado_en FROM usuarios")
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]
 
 
# ─── GET /api/usuarios/{nombre} ───────────────────────────────────────────────
@router.get("/usuarios/{nombre}")
def obtener_usuario(nombre: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, activo, creado_en FROM usuarios WHERE nombre = %s",
        (nombre.lower(),)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
 
    return dict(row)
 
 
# ─── DELETE /api/usuarios/{nombre} ────────────────────────────────────────────
@router.delete("/usuarios/{nombre}")
def eliminar_usuario(nombre: str):
    nombre = nombre.lower()
    conn = get_connection()
    cursor = conn.cursor()

    delete_voice(nombre) #Elimina la voz almacenada localmente

    cursor.execute("DELETE FROM usuarios WHERE nombre = %s RETURNING id", (nombre,))#Elimina el usuario de la db
    eliminado = cursor.fetchone()
    conn.commit() #Confirmacion de cambios
    conn.close()

    if not eliminado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en BD")

    return {"success": True, "message": f"Usuario '{nombre}' eliminado"}
 
 
# ─── GET /api/logs ────────────────────────────────────────────────────────────
@router.get("/logs")
def obtener_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM logs_acceso ORDER BY fecha DESC LIMIT 50"
    ) #Consulta para obtener todos los logs de acceso
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
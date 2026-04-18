from fastapi import UploadFile
from pathlib import Path
import uuid

# Carpeta donde se guardan audios temporales
TEMP_DIR = Path(__file__).parent.parent / "temp_audio"
TEMP_DIR.mkdir(exist_ok=True)


async def save_temp_audio(audio: UploadFile, prefix: str = "audio") -> Path:

    #Guarda un archivo de audio recibido del frontend de forma temporal.
    

    # Nombre único para evitar colisiones si hay peticiones simultáneas
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.wav"
    path = TEMP_DIR / filename

    content = await audio.read()
    with open(path, "wb") as f: 
        f.write(content)

    return path #Retorna la ruta donde se guardo


def delete_temp_audio(path: Path):
    #Elimina un archivo de audio temporal después de procesarlo.
    try:
        if path.exists(): #Verifica que el archivo existe
            path.unlink() #Elimina el archivo
    except Exception as e:
        print(f"⚠️ No se pudo eliminar {path}: {e}")
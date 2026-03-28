from fastapi import UploadFile
from pathlib import Path
import uuid

# Carpeta donde se guardan audios temporales
TEMP_DIR = Path(__file__).parent.parent / "temp_audio"
TEMP_DIR.mkdir(exist_ok=True)


async def save_temp_audio(audio: UploadFile, prefix: str = "audio") -> Path:
    """
    Guarda un archivo de audio recibido del frontend de forma temporal.
    Retorna la ruta donde fue guardado.
    """
    # Nombre único para evitar colisiones si hay peticiones simultáneas
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.wav"
    path = TEMP_DIR / filename

    content = await audio.read()
    with open(path, "wb") as f:
        f.write(content)

    return path


def delete_temp_audio(path: Path):
    """Elimina un archivo de audio temporal después de procesarlo."""
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        print(f"⚠️ No se pudo eliminar {path}: {e}")
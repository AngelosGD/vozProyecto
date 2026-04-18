import torch
import torchaudio
import soundfile as sf
import numpy as np
from pathlib import Path
from speechbrain.inference.speaker import EncoderClassifier
from speechbrain.utils.fetching import LocalStrategy


  
  
VOICES_DB_PATH = Path(__file__).parent / "voices_db"
THRESHOLD = 0.30  

VOICES_DB_PATH.mkdir(exist_ok=True)

encoder = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb",
    local_strategy=LocalStrategy.COPY
)

# Rutas y configuracion
# VOICES_DB_PATH: carpeta donde se guardan las voces registradas
# THRESHOLD: valor minimo de similitud para reconocer una voz 0.30 es bastante restrictivo

# Funciones principales para registrar login y gestionar voces

def register_voice(name: str, audio_path: str) -> dict:
    # Registra una nueva voz en la base de datos
    # Extrae las caracteristicas del audio y las guarda en un archivo
    # name: nombre del usuario a registrar
    # audio_path: ruta del archivo de audio
    try:
        embedding = _get_embedding(audio_path)
        save_path = VOICES_DB_PATH / f"{name}.npy"
        np.save(save_path, embedding)
        return {"success": True, "message": f"Voz registrada para '{name}'"}
    except Exception as e:
        return {"success": False, "message": f"Error al registrar: {str(e)}"}


def login_voice(audio_path: str) -> dict:
    # Verifica si el audio del usuario coincide con alguna voz registrada
    # Compara la voz con todos los registros y devuelve el mejor resultado
    # Devuelve exito solo si la similitud supera el threshold
    registered = list(VOICES_DB_PATH.glob("*.npy"))

    if not registered:
        return {"success": False, "message": "No hay voces registradas aun"}

    try:
        embedding = _get_embedding(audio_path)
        best_match = None
        best_score = -1

        for voice_file in registered:
            saved_embedding = np.load(voice_file)
            score = _cosine_similarity(embedding, saved_embedding)
            if score > best_score:
                best_score = score
                best_match = voice_file.stem

        if best_score >= THRESHOLD:
            return {
                "success": True,
                "match": best_match,
                "confidence": round(float(best_score), 4),
                "message": f"Bienvenido, {best_match}!"
            }
        else:
            return {
                "success": False,
                "match": None,
                "confidence": round(float(best_score), 4),
                "message": "Voz no reconocida"
            }

    except Exception as e:
        return {"success": False, "message": f"Error al procesar audio: {str(e)}"}


def list_registered_users() -> list:
    # Devuelve una lista con los nombres de todos los usuarios registrados
    # Lee los nombres de los archivos guardados en la carpeta de voces
    return [f.stem for f in VOICES_DB_PATH.glob("*.npy")]


def delete_voice(name: str) -> dict:
    # Elimina una voz registrada del sistema
    # Busca el archivo del usuario y lo elimina si existe
    path = VOICES_DB_PATH / f"{name}.npy"
    if not path.exists():
        return {"success": False, "message": f"Usuario '{name}' no encontrado"}
    path.unlink()
    return {"success": True, "message": f"Voz de '{name}' eliminada"}


# Funciones utiles internas

def _get_embedding(audio_path: str) -> np.ndarray:
    # Extrae las caracteristicas unicas de una voz desde un archivo de audio
    # Lee el audio carga en el modelo y obtiene un vector que representa la voz
    # Convierte cualquier audio a 16000 Hz que es lo que espera el modelo
    data, fs = sf.read(audio_path, dtype="float32")

    if data.ndim > 1:
        data = data.mean(axis=1)

    signal = torch.tensor(data).unsqueeze(0)

    if fs != 16000:
        resampler = torchaudio.transforms.Resample(fs, 16000)
        signal = resampler(signal)

    with torch.no_grad():
        embedding = encoder.encode_batch(signal)

    return embedding.squeeze().numpy()


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    # Calcula la similitud entre dos vectores de voz
    # Devuelve un valor entre -1 y 1 donde 1 significa voces identicas
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
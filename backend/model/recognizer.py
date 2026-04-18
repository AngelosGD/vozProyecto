import torch
import torchaudio
import soundfile as sf
import numpy as np
from pathlib import Path
from speechbrain.inference.speaker import EncoderClassifier
from speechbrain.utils.fetching import LocalStrategy

# ─── Configuración ────────────────────────────────────────────────────────────
VOICES_DB_PATH = Path(__file__).parent / "voices_db"
THRESHOLD = 0.20  # Score mínimo para considerar match (0 a 1)

VOICES_DB_PATH.mkdir(exist_ok=True)

# Se carga el modelo una sola vez (la primera vez descarga ~100MB automático)
# LocalStrategy.COPY evita el problema de symlinks en Windows
encoder = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb",
    local_strategy=LocalStrategy.COPY
)


# ─── Funciones principales ────────────────────────────────────────────────────

def register_voice(name: str, audio_path: str) -> dict:
    try:
        embedding = _get_embedding(audio_path)
        save_path = VOICES_DB_PATH / f"{name}.npy"
        np.save(save_path, embedding)
        return {"success": True, "message": f"Voz registrada para '{name}'"}
    except Exception as e:
        return {"success": False, "message": f"Error al registrar: {str(e)}"}


def login_voice(audio_path: str) -> dict:
    registered = list(VOICES_DB_PATH.glob("*.npy"))

    if not registered:
        return {"success": False, "message": "No hay voces registradas aún"}

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
    return [f.stem for f in VOICES_DB_PATH.glob("*.npy")]


def delete_voice(name: str) -> dict:
    path = VOICES_DB_PATH / f"{name}.npy"
    if not path.exists():
        return {"success": False, "message": f"Usuario '{name}' no encontrado"}
    path.unlink()
    return {"success": True, "message": f"Voz de '{name}' eliminada"}


# ─── Utilidades internas ──────────────────────────────────────────────────────

def _get_embedding(audio_path: str) -> np.ndarray:
    """Carga un audio y lo convierte en un embedding con soundfile (compatible Windows)."""
    data, fs = sf.read(audio_path, dtype="float32")

    # Si es stereo lo convierte a mono
    if data.ndim > 1:
        data = data.mean(axis=1)

    signal = torch.tensor(data).unsqueeze(0)  # shape: [1, samples]

    # Speechbrain espera 16000 Hz
    if fs != 16000:
        resampler = torchaudio.transforms.Resample(fs, 16000)
        signal = resampler(signal)

    with torch.no_grad():
        embedding = encoder.encode_batch(signal)

    return embedding.squeeze().numpy()


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
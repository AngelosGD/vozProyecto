"""
Script de prueba para el modelo de reconocimiento de voz.
Úsalo para probar recognizer.py sin necesitar el backend ni el frontend.
"""

import sounddevice as sd
from scipy.io.wavfile import write
from recognizer import register_voice, login_voice, list_registered_users, delete_voice

# ─── Configuración de grabación ───────────────────────────────────────────────
SAMPLE_RATE = 16000  # Hz (speechbrain espera 16000)
DURATION = 4         # segundos de grabación
TEMP_FILE = "temp_audio.wav"


def grabar_audio(duracion: int = DURATION) -> str:
    """Graba audio desde el micrófono y lo guarda en un .wav temporal."""
    print(f"\n🎙️  Grabando {duracion} segundos... habla ahora!")
    audio = sd.rec(int(duracion * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    write(TEMP_FILE, SAMPLE_RATE, audio)
    print("✅ Grabación terminada\n")
    return TEMP_FILE


def menu():
    print("\n============================")
    print("  TEST - Reconocimiento de voz")
    print("============================")
    print("1. Registrar nueva voz")
    print("2. Iniciar sesión por voz")
    print("3. Ver usuarios registrados")
    print("4. Eliminar usuario")
    print("5. Salir")
    return input("\nElige una opción: ").strip()


def main():
    while True:
        opcion = menu()

        if opcion == "1":
            nombre = input("¿Nombre de usuario a registrar? ").strip().lower()
            if not nombre:
                print("❌ Nombre inválido")
                continue
            audio = grabar_audio()
            resultado = register_voice(nombre, audio)
            print(f"\n📋 Resultado: {resultado}")

        elif opcion == "2":
            audio = grabar_audio()
            resultado = login_voice(audio)
            print(f"\n📋 Resultado: {resultado}")

        elif opcion == "3":
            usuarios = list_registered_users()
            if usuarios:
                print(f"\n👥 Usuarios registrados: {', '.join(usuarios)}")
            else:
                print("\n⚠️  No hay usuarios registrados")

        elif opcion == "4":
            nombre = input("¿Nombre de usuario a eliminar? ").strip().lower()
            resultado = delete_voice(nombre)
            print(f"\n📋 Resultado: {resultado}")

        elif opcion == "5":
            print("Adiós 👋")
            break

        else:
            print("❌ Opción no válida")


if __name__ == "__main__":
    main()
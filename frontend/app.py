import customtkinter as ctk
import sounddevice as sd
from scipy.io.wavfile import write
import requests
import threading
import time
from urllib.parse import quote

# ─── Config ───────────────────────────────────────────────────────────────────
API = "http://localhost:8000/api"
SAMPLE_RATE = 16000
DURATION = 4

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# ─── App ──────────────────────────────────────────────────────────────────────
class VozAuthApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VozAuth")
        self.geometry("480x750")
        self.minsize(480, 750)
        self.resizable(True, True)

        self.audio_path = "temp_voz.wav"
        self.audio_ready = False
        self.is_recording = False
        self.current_user = None

        self.show_login()

    # ── Crear scroll container ────────────────────────────────────────────────
    def make_scroll(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        return scroll

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ═══════════════════════════════════════════════════════════════════════════
    # LOGIN
    # ═══════════════════════════════════════════════════════════════════════════
    def fetch_users(self):
        try:
            res = requests.get(f"{API}/usuarios")
            return res.json() if res.ok else []
        except Exception:
            return []

    def delete_user(self, nombre: str):
        try:
            url = f"{API}/usuarios/{quote(nombre)}"
            res = requests.delete(url)
            data = res.json()
            if res.ok:
                self.show_result(f"✅ Usuario '{nombre}' eliminado", "success")
                self.show_admin_screen(self.current_user)
            else:
                self.show_result(f"❌ {data.get('detail') or data.get('message', 'No se pudo eliminar')}", "error")
        except Exception:
            self.show_result("Error eliminando usuario", "error")

    def show_login(self):
        self.clear()
        self.audio_ready = False
        self.is_recording = False

        f = self.make_scroll()

        ctk.CTkLabel(f, text="🔐", font=ctk.CTkFont(size=56)).pack(pady=(40, 4))
        ctk.CTkLabel(f, text="Acceso por Voz",
                     font=ctk.CTkFont(size=24, weight="bold")).pack()
        ctk.CTkLabel(f, text="Verifica tu identidad con tu voz",
                     text_color="gray", font=ctk.CTkFont(size=13)).pack(pady=(4, 24))

        # Caja de estado
        box = ctk.CTkFrame(f, corner_radius=12)
        box.pack(padx=32, fill="x", pady=(0, 16))
        ctk.CTkLabel(box, text="🛡️", font=ctk.CTkFont(size=32)).pack(pady=(20, 4))
        self.status_title = ctk.CTkLabel(box, text="Listo para verificar",
                                          font=ctk.CTkFont(size=15, weight="bold"))
        self.status_title.pack()
        self.status_sub = ctk.CTkLabel(box, text="Presiona el botón y di la frase",
                                        text_color="gray", font=ctk.CTkFont(size=12))
        self.status_sub.pack(pady=(2, 20))

        # Frase
        ctk.CTkLabel(f, text="Di la frase de verificación:",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack()
        ctk.CTkLabel(f, text='"Mi voz es mi contraseña"',
                     text_color="#4ade80",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(4, 20))

        # Timer
        self.timer_label = ctk.CTkLabel(f, text="", text_color="#ef4444",
                                         font=ctk.CTkFont(size=12))
        self.timer_label.pack()

        # Botón mic
        self.mic_btn = ctk.CTkButton(f, text="🎙️  Grabar voz", height=48,
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      command=lambda: self.grabar("login"))
        self.mic_btn.pack(padx=32, fill="x", pady=(4, 10))

        # Botón verificar
        self.submit_btn = ctk.CTkButton(f, text="Verificar identidad →", height=48,
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         state="disabled", command=self.submit_login)
        self.submit_btn.pack(padx=32, fill="x")

        # Resultado
        self.result_label = ctk.CTkLabel(f, text="", font=ctk.CTkFont(size=13))
        self.result_label.pack(pady=(14, 0))

        # Footer
        ctk.CTkLabel(f, text="¿No tienes cuenta?",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=(24, 0))
        ctk.CTkButton(f, text="Registrarse", fg_color="transparent",
                      text_color="#4ade80", hover=False,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.show_register).pack(pady=(0, 32))

    # ═══════════════════════════════════════════════════════════════════════════
    # REGISTER
    # ═══════════════════════════════════════════════════════════════════════════
    def show_register(self):
        self.clear()
        self.audio_ready = False
        self.is_recording = False

        f = self.make_scroll()

        ctk.CTkLabel(f, text="👤", font=ctk.CTkFont(size=56)).pack(pady=(40, 4))
        ctk.CTkLabel(f, text="Registro de Usuario",
                     font=ctk.CTkFont(size=24, weight="bold")).pack()
        ctk.CTkLabel(f, text="Crea tu perfil de voz para autenticación",
                     text_color="gray", font=ctk.CTkFont(size=13)).pack(pady=(4, 24))

        # Steps
        steps_frame = ctk.CTkFrame(f, fg_color="transparent")
        steps_frame.pack(pady=(0, 24))
        self.step_labels = []
        for i, txt in enumerate(["1", "2", "3"]):
            s = ctk.CTkLabel(steps_frame, text=txt, width=36, height=36,
                             corner_radius=18,
                             fg_color="#4ade80" if i == 0 else "#2a2a2a",
                             text_color="#000" if i == 0 else "gray",
                             font=ctk.CTkFont(size=13, weight="bold"))
            s.grid(row=0, column=i*2, padx=4)
            self.step_labels.append(s)
            if i < 2:
                ctk.CTkLabel(steps_frame, text="──", text_color="gray",
                             font=ctk.CTkFont(size=12)).grid(row=0, column=i*2+1)

        # Input nombre
        ctk.CTkLabel(f, text="Nombre de usuario", anchor="w",
                     font=ctk.CTkFont(size=13)).pack(padx=32, fill="x")
        self.input_nombre = ctk.CTkEntry(f, placeholder_text="ej: juan_garcia", height=44)
        self.input_nombre.pack(padx=32, fill="x", pady=(6, 20))

        # Frase
        ctk.CTkLabel(f, text="Di la siguiente frase:",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack()
        ctk.CTkLabel(f, text='"Mi voz es mi contraseña"',
                     text_color="#4ade80",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(4, 20))

        # Timer
        self.timer_label = ctk.CTkLabel(f, text="", text_color="#ef4444",
                                         font=ctk.CTkFont(size=12))
        self.timer_label.pack()

        # Botón mic
        self.mic_btn = ctk.CTkButton(f, text="🎙️  Grabar voz", height=48,
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      command=lambda: self.grabar("register"))
        self.mic_btn.pack(padx=32, fill="x", pady=(4, 10))

        # Botón registrar
        self.submit_btn = ctk.CTkButton(f, text="Registrar usuario →", height=48,
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         state="disabled", command=self.submit_register)
        self.submit_btn.pack(padx=32, fill="x")

        # Resultado
        self.result_label = ctk.CTkLabel(f, text="", font=ctk.CTkFont(size=13))
        self.result_label.pack(pady=(14, 0))

        # Footer
        ctk.CTkLabel(f, text="¿Ya tienes cuenta?",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=(24, 0))
        ctk.CTkButton(f, text="Iniciar sesión", fg_color="transparent",
                      text_color="#4ade80", hover=False,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.show_login).pack(pady=(0, 32))

    # ═══════════════════════════════════════════════════════════════════════════
    # GRABAR
    # ═══════════════════════════════════════════════════════════════════════════
    def grabar(self, mode):
        if self.is_recording:
            return
        self.is_recording = True
        self.audio_ready = False
        self.submit_btn.configure(state="disabled")
        threading.Thread(target=self._grabar_thread, args=(mode,), daemon=True).start()

    def _grabar_thread(self, mode):
        for i in range(DURATION, 0, -1):
            self.mic_btn.configure(text=f"🔴  Grabando... {i}s", state="disabled")
            self.timer_label.configure(text=f"⏱ {i}s")
            time.sleep(1)

        audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                       channels=1, dtype="int16")
        sd.wait()
        write(self.audio_path, SAMPLE_RATE, audio)

        self.audio_ready = True
        self.is_recording = False
        self.mic_btn.configure(text="✅  Audio grabado — grabar de nuevo", state="normal")
        self.timer_label.configure(text="")
        self.submit_btn.configure(state="normal")

    # ═══════════════════════════════════════════════════════════════════════════
    # SUBMIT LOGIN
    # ═══════════════════════════════════════════════════════════════════════════
    def submit_login(self):
        if not self.audio_ready:
            self.show_result("Graba tu voz primero", "error")
            return
        self.submit_btn.configure(state="disabled", text="Verificando...")
        threading.Thread(target=self._login_thread, daemon=True).start()

    def _login_thread(self):
        try:
            with open(self.audio_path, "rb") as f:
                res = requests.post(f"{API}/login-voz",
                                    files={"audio": ("voz.wav", f, "audio/wav")})
            data = res.json()
            print(f"Respuesta del servidor: {data}")  # ← agrega esta línea

            if data.get("success"):
                self.result_label.configure(text="")
                self.show_admin_screen(data.get("match"))
                self.status_title.configure(text="¡Acceso permitido!")
                self.status_sub.configure(text=f"Identificado como {data['match']}")
                return
            else:
                self.show_result(f"❌ {data.get('message', 'Voz no reconocida')}", "error")
                self.status_title.configure(text="No reconocido")
                self.status_sub.configure(text="Intenta de nuevo hablando más claro")
                self.submit_btn.configure(state="normal", text="Verificar identidad →")
        except Exception:
            self.show_result("", "error")
            self.submit_btn.configure(state="normal", text="Verificar identidad →")

    def show_admin_screen(self, match_name: str):
        self.clear()
        self.current_user = match_name

        f = self.make_scroll()

        ctk.CTkLabel(f, text="👑", font=ctk.CTkFont(size=56)).pack(pady=(40, 4))
        ctk.CTkLabel(f, text="Bienvenido Admin",
                     font=ctk.CTkFont(size=24, weight="bold")).pack()
        ctk.CTkLabel(f, text=f"Usuario reconocido: {match_name}",
                     text_color="gray", font=ctk.CTkFont(size=13)).pack(pady=(4, 8))
        self.result_label = ctk.CTkLabel(f, text="", font=ctk.CTkFont(size=13))
        self.result_label.pack(pady=(0, 12))

        box = ctk.CTkFrame(f, corner_radius=12)
        box.pack(padx=32, fill="x", pady=(0, 16))
        ctk.CTkLabel(box, text="Acceso exitoso",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(box, text="Has ingresado correctamente como administrador.",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=(0, 20))

        users = self.fetch_users()
        ctk.CTkLabel(f, text=f"Usuarios registrados: {len(users)}",
                     text_color="#a3a3a3", font=ctk.CTkFont(size=13)).pack(pady=(0, 10))

        users_frame = ctk.CTkFrame(f, fg_color="#141414", corner_radius=12)
        users_frame.pack(padx=32, fill="both", expand=True, pady=(0, 16))

        if not users:
            ctk.CTkLabel(users_frame, text="No hay usuarios registrados.",
                         text_color="gray", font=ctk.CTkFont(size=13)).pack(pady=20)
        else:
            for user in users:
                row = ctk.CTkFrame(users_frame, fg_color="#1f1f1f", corner_radius=10)
                row.pack(fill="x", padx=10, pady=8)

                ctk.CTkLabel(row, text=user["nombre"], anchor="w",
                             font=ctk.CTkFont(size=13)).pack(side="left", padx=(12, 0), pady=10, expand=True, fill="x")
                ctk.CTkButton(row, text="Eliminar", width=90, height=36,
                              fg_color="#ef4444", hover_color="#e11d48",
                              command=lambda nombre=user["nombre"]: self.delete_user(nombre)).pack(side="right", padx=12, pady=10)

        action_frame = ctk.CTkFrame(f, fg_color="transparent")
        action_frame.pack(padx=32, fill="x", pady=(0, 20))
        ctk.CTkButton(action_frame, text="Refrescar lista", height=44,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=lambda: self.show_admin_screen(self.current_user)).pack(side="left", expand=True, fill="x")
        ctk.CTkButton(action_frame, text="Salir", height=44,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.show_login).pack(side="left", expand=True, fill="x", padx=(12, 0))

    # ═══════════════════════════════════════════════════════════════════════════
    # SUBMIT REGISTER
    # ═══════════════════════════════════════════════════════════════════════════
    def submit_register(self):
        nombre = self.input_nombre.get().strip().lower()
        if not nombre:
            self.show_result("Ingresa tu nombre primero", "error")
            return
        if not self.audio_ready:
            self.show_result("Graba tu voz primero", "error")
            return
        self.submit_btn.configure(state="disabled", text="Registrando...")
        threading.Thread(target=self._register_thread, args=(nombre,), daemon=True).start()

    def _register_thread(self, nombre):
        try:
            with open(self.audio_path, "rb") as f:
                res = requests.post(f"{API}/usuarios",
                                    data={"nombre": nombre},
                                    files={"audio": ("voz.wav", f, "audio/wav")})
            data = res.json()
            if res.ok and data.get("success"):
                self.show_result(f"✅ Usuario '{nombre}' registrado correctamente", "success")
                self.after(2000, self.show_login)
            else:
                self.show_result(f"❌ {data.get('detail') or data.get('message', 'Error al registrar')}", "error")
                self.submit_btn.configure(state="normal", text="Registrar usuario →")
        except Exception:
            self.show_result("Error conectando al servidor", "error")
            self.submit_btn.configure(state="normal", text="Registrar usuario →")

    def show_result(self, msg, type="info"):
        color = "#4ade80" if type == "success" else "#ef4444" if type == "error" else "white"
        self.result_label.configure(text=msg, text_color=color)


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = VozAuthApp()
    app.mainloop()
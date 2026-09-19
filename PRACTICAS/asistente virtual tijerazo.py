import tkinter as tk
import speech_recognition as sr
import pyttsx3
import threading
import queue

RESPUESTAS = {
    "tcp_app": {"txt": "Capa de aplicación. Interfaz directa al usuario como HTTP.", "q": "¿Sabes qué puerto utiliza el protocolo HTTP?"},
    "tcp_trans": {"txt": "Capa de transporte. TCP garantiza entrega y UDP es rápido.", "q": "¿En qué casos usarías UDP en lugar de TCP?"},
    "tcp_red": {"txt": "Capa de Red. Enrutamiento de paquetes usando IP.", "q": "¿Conoces la diferencia principal entre IPv4 e IPv6?"},
    "tcp_enl": {"txt": "Capa de Enlace. Direcciones MAC y transmisión física.", "q": "¿Sabes cuántos bits conforman una dirección MAC?"},
    
    "osi_app": {"txt": "Capa 7, Aplicación. Interfaz con el software.", "q": "¿Qué protocolo se usa para enviar correos?"},
    "osi_pres": {"txt": "Capa 6, Presentación. Traduce, comprime y cifra.", "q": "¿Conoces algún algoritmo de cifrado común?"},
    "osi_ses": {"txt": "Capa 5, Sesión. Mantiene el diálogo entre dispositivos.", "q": "¿Qué pasa si la sesión caduca en tu banco?"},
    "osi_trans": {"txt": "Capa 4, Transporte. Gestiona puertos y entrega.", "q": "¿Sabías que los firewalls operan en esta capa?"},
    "osi_red": {"txt": "Capa 3, Red. Routers y mejor ruta lógica.", "q": "¿Qué comando usarías para ver la ruta de los paquetes?"},
    "osi_enl": {"txt": "Capa 2, Enlace. Acceso al medio mediante tramas.", "q": "¿Diferencia física entre un switch y un hub?"},
    "osi_fis": {"txt": "Capa 1, Física. Pulsos eléctricos o luz.", "q": "¿A qué se refiere el término atenuación?"},
    
    "dir_cla": {"txt": "Clases. Primer octeto de la IP. A, B o C.", "q": "¿Para qué sirve la dirección especial localhost?"},
    "dir_mas": {"txt": "Máscaras. Definen red y hosts.", "q": "¿Qué significa la diagonal 24 en una IP?"},
    "dir_pri": {"txt": "Límites. ID de red y Broadcast.", "q": "¿Por qué no asignas la dirección de broadcast a un host?"},
    "dir_hos": {"txt": "Cálculo de Hosts. Fórmula 2 a la n, menos 2.", "q": "¿Por qué restamos dos a la fórmula?"}
}

class TijeraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tijera AI - Tutor Pro")
        self.root.geometry("900x700")
        self.root.configure(bg="#0a0e1a")
        
        self.estado = 0
        self.caso_activo = ""
        self.is_talking = False  
        
        self.r = sr.Recognizer()
        self.mic = sr.Microphone()
        self.tts_queue = queue.Queue()
        
        self.build_ui()
        
        threading.Thread(target=self.tts_worker, daemon=True).start()
        threading.Thread(target=self.init_mic, daemon=True).start()

    def build_ui(self):
        tk.Label(self.root, text="🔑 CLAVE: TIJERA", bg="#0a0e1a", fg="#00f5d4", font=("Consolas", 10, "bold"), pady=10).pack()
        tk.Label(self.root, text="TIJERAZO", bg="#0a0e1a", fg="#e2e8f0", font=("Segoe UI", 32, "bold")).pack()
        tk.Label(self.root, text="Tutor Multinivel · Escucha Activa", bg="#0a0e1a", fg="#64748b", font=("Consolas", 10)).pack(pady=(0, 10))

        self.lbl_main = tk.Label(self.root, text="Menú Principal: Calibrando...", bg="#00f5d4", fg="#0a0e1a", font=("Segoe UI", 14, "bold"), padx=20, pady=10)
        self.lbl_main.pack(pady=10)

        self.frame_casos = tk.Frame(self.root, bg="#0a0e1a")
        self.frame_casos.pack(pady=10, fill="x", padx=40)
        
        self.btn_tcp = tk.Label(self.frame_casos, text="📡 TCP/IP\n(Caso 1)", bg="#111827", fg="#00f5d4", font=("Segoe UI", 12, "bold"), bd=2, relief="ridge", width=20, pady=15)
        self.btn_tcp.grid(row=0, column=0, padx=10)
        
        self.btn_osi = tk.Label(self.frame_casos, text="🧩 Modelo OSI\n(Caso 2)", bg="#111827", fg="#f72585", font=("Segoe UI", 12, "bold"), bd=2, relief="ridge", width=20, pady=15)
        self.btn_osi.grid(row=0, column=1, padx=10)
        
        self.btn_dir = tk.Label(self.frame_casos, text="🔢 IP Clases\n(Caso 3)", bg="#111827", fg="#ffd60a", font=("Segoe UI", 12, "bold"), bd=2, relief="ridge", width=20, pady=15)
        self.btn_dir.grid(row=0, column=2, padx=10)
        self.frame_casos.grid_columnconfigure((0,1,2), weight=1)

        self.frame_opciones = tk.Frame(self.root, bg="#0a0e1a")

        self.frame_detalle = tk.Frame(self.root, bg="#0d1526", bd=1, relief="solid", highlightbackground="#1e2d45")
        self.lbl_detalle_titulo = tk.Label(self.frame_detalle, text="", bg="#0d1526", fg="#e2e8f0", font=("Segoe UI", 14, "bold"))
        self.lbl_detalle_titulo.pack(pady=(15,5))
        self.lbl_detalle_texto = tk.Label(self.frame_detalle, text="", bg="#0d1526", fg="#e2e8f0", font=("Consolas", 11), wraplength=700, justify="center")
        self.lbl_detalle_texto.pack(pady=(0,15), padx=20)

        self.lbl_status = tk.Label(self.root, text="🔴 Calibrando ruido de fondo (1 segundo)...", bg="#111827", fg="#64748b", font=("Consolas", 10), pady=10)
        self.lbl_status.pack(side="bottom", fill="x")

    def mostrar_opciones_caso(self, caso, color):
        for widget in self.frame_opciones.winfo_children():
            widget.destroy()
            
        opciones = []
        if caso == "tcp":
            opciones = ["Aplicación", "Transporte", "Red", "Enlace y Física"]
        elif caso == "osi":
            opciones = ["7. Aplicación", "6. Presentación", "5. Sesión", "4. Transporte", "3. Red", "2. Enlace", "1. Física"]
        elif caso == "dir":
            opciones = ["I. Clases", "II. Máscaras", "III. Límites", "IV. Hosts"]
            
        for opt in opciones:
            tk.Label(self.frame_opciones, text=f"• {opt}", bg="#111827", fg=color, font=("Consolas", 12, "bold"), pady=6, padx=15, relief="groove", bd=1).pack(fill="x", pady=3)
            
        self.frame_opciones.pack(pady=10, fill="x", padx=120)

    def init_mic(self):
        with self.mic as source:
            self.r.adjust_for_ambient_noise(source, duration=1)
        self.root.after(0, self.iniciar_escucha_perpetua)

    def iniciar_escucha_perpetua(self):
        self.lbl_main.config(text="Menú Principal: Di 'Tijera'")
        self.lbl_status.config(text="🟢 Micrófono Activo - Escuchando en 2do plano...", fg="#00f5d4")
        self.is_talking = False
        self.r.listen_in_background(self.mic, self.audio_callback, phrase_time_limit=5)

    def tts_worker(self):
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        
        while True:
            texto, callback = self.tts_queue.get()
            self.is_talking = True 
            
            engine.say(texto)
            engine.runAndWait()
            
            self.is_talking = False 
            self.root.after(0, lambda: self.lbl_status.config(text="🟢 Micrófono Activo - Esperando tu respuesta...", fg="#00f5d4"))
            
            if callback:
                self.root.after(0, callback)
            self.tts_queue.task_done()

    def hablar(self, texto, callback=None):
        self.lbl_status.config(text="🔊 Hablando...", fg="#f72585")
        self.tts_queue.put((texto, callback))

    def audio_callback(self, recognizer, audio):
        if getattr(self, 'is_talking', False):
            return 
            
        try:
            texto_crudo = recognizer.recognize_google(audio, language="es-MX")
            self.root.after(0, self.procesar_texto, texto_crudo)
        except sr.UnknownValueError:
            pass  
        except Exception as e:
            print("Error de audio:", e)

    def reset_visuals(self):
        self.btn_tcp.config(bg="#111827", fg="#00f5d4")
        self.btn_osi.config(bg="#111827", fg="#f72585")
        self.btn_dir.config(bg="#111827", fg="#ffd60a")
        self.frame_detalle.pack_forget()
        self.frame_opciones.pack_forget()
        self.lbl_main.config(text="Menú Principal: Escuchando...", bg="#00f5d4", fg="#0a0e1a")

    def volver_al_menu(self):
        self.estado = 1
        self.caso_activo = ""
        self.reset_visuals()
        self.hablar("Regresando al menú principal. ¿Qué otro caso deseas revisar?")

    def mostrar_nodo(self, titulo, llave, color):
        self.estado = 3
        datos = RESPUESTAS[llave]
        
        self.frame_opciones.pack_forget()
        
        self.frame_detalle.pack(fill="x", padx=40, pady=20)
        self.lbl_detalle_titulo.config(text=f"▶ {titulo.upper()}", fg=color)
        self.lbl_detalle_texto.config(text=f"{datos['txt']}\n\nPREGUNTA: {datos['q']}")
        
        def ir_a_nivel_4():
            self.estado = 4
            self.lbl_main.config(text="Nivel 4: Esperando tu respuesta...", bg=color)
            
        self.hablar(f"{datos['txt']} {datos['q']}", ir_a_nivel_4)

    def procesar_texto(self, text_raw):
        text = text_raw.lower()
        text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        
        self.lbl_status.config(text=f"🟢 Escuché: '{text_raw}'")

        if self.estado == 0 and "tijera" in text:
            self.estado = 1
            self.lbl_main.config(text="Tijera Activada: Elige un Caso", bg="#f72585", fg="white")
            self.hablar("Tijera activada. ¿Qué caso deseas revisar: Caso uno, dos o tres?")
            return

        if self.estado == 4:
            self.hablar("Excelente. Cerrando tema.", self.volver_al_menu)
            return

        if self.estado == 1:
            if "uno" in text or "tcp" in text:
                self.caso_activo = "tcp"
                self.estado = 2
                self.btn_tcp.config(bg="#00f5d4", fg="#0a0e1a")
                self.lbl_main.config(text="Caso 1: TCP/IP", bg="#00f5d4")
                self.mostrar_opciones_caso("tcp", "#00f5d4")
                self.hablar("Caso 1. TCP IP. Las opciones son: Aplicacion, transporte, red, o enlace y fisica. ¿Cuál eliges?")
            elif "dos" in text or "osi" in text:
                self.caso_activo = "osi"
                self.estado = 2
                self.btn_osi.config(bg="#f72585", fg="#0a0e1a")
                self.lbl_main.config(text="Caso 2: Modelo OSI", bg="#f72585")
                self.mostrar_opciones_caso("osi", "#f72585")
                self.hablar("Caso 2. Modelo OSI. Tenemos las capas: Aplicacion, presentacion, sesion, transporte, red, enlace, y fisica. ¿Cuál quieres revisar?")
            elif "tres" in text or "direccionamiento" in text or "clases" in text:
                self.caso_activo = "dir"
                self.estado = 2
                self.btn_dir.config(bg="#ffd60a", fg="#0a0e1a")
                self.lbl_main.config(text="Caso 3: IP Clases", bg="#ffd60a")
                self.mostrar_opciones_caso("dir", "#ffd60a")
                self.hablar("Caso 3. Direccionamiento con clases. Puedes elegir entre: Clases, mascaras, limites o hosts. ¿Cuál necesitas?")
            return

        if self.estado == 2:
            if self.caso_activo == "tcp":
                if "aplicacion" in text: self.mostrar_nodo("Aplicación", "tcp_app", "#00f5d4")
                elif "transporte" in text: self.mostrar_nodo("Transporte", "tcp_trans", "#00f5d4")
                elif "red" in text: self.mostrar_nodo("Red", "tcp_red", "#00f5d4")
                elif "enlace" in text or "fisica" in text: self.mostrar_nodo("Enlace", "tcp_enl", "#00f5d4")
            
            elif self.caso_activo == "osi":
                if "aplicacion" in text: self.mostrar_nodo("Aplicación", "osi_app", "#f72585")
                elif "presentacion" in text: self.mostrar_nodo("Presentación", "osi_pres", "#f72585")
                elif "sesion" in text: self.mostrar_nodo("Sesión", "osi_ses", "#f72585")
                elif "transporte" in text: self.mostrar_nodo("Transporte", "osi_trans", "#f72585")
                elif "red" in text: self.mostrar_nodo("Red", "osi_red", "#f72585")
                elif "enlace" in text: self.mostrar_nodo("Enlace", "osi_enl", "#f72585")
                elif "fisica" in text: self.mostrar_nodo("Física", "osi_fis", "#f72585")
            
            elif self.caso_activo == "dir":
                if "clase" in text: self.mostrar_nodo("Clases", "dir_cla", "#ffd60a")
                elif "mascara" in text: self.mostrar_nodo("Máscaras", "dir_mas", "#ffd60a")
                elif "limite" in text or "ultima" in text or "primera" in text: self.mostrar_nodo("Límites", "dir_pri", "#ffd60a")
                elif "host" in text: self.mostrar_nodo("Hosts", "dir_hos", "#ffd60a")

if __name__ == "__main__":
    root = tk.Tk()
    app = TijeraApp(root)
    root.mainloop()
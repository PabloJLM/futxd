import customtkinter
from PIL import Image, ImageTk
import time
import subprocess
import sys
import os
import config_camara
import threading

logo_path = "logo.png"
imagen_central = "centro.png"

def actualizar_wifi():
    def tarea():
        ssid = wifi()
        red_label.configure(text=f" {ssid}")
    threading.Thread(target=tarea, daemon=True).start()

def wifi():
    try: 
        wifi = subprocess.check_output("netsh wlan show interfaces", shell=True).decode("utf-8")
        for linea in wifi.splitlines():
            if "SSID" in linea and "BSSID" not in linea:
                return linea.split(":")[1].strip()
        return "No conectado"
    except:
        return "Error!"

def actualizar_reloj():
    hora_actual = time.strftime("%H:%M:%S")
    reloj_label.configure(text=hora_actual)
    app.after(1000, actualizar_reloj)

def abrir_seleccion_campo():
    from esquinas import VentanaEsquinas
    sel_campo = VentanaEsquinas()  
    sel_campo.lift()                
    sel_campo.focus_force()        
    sel_campo.grab_set()    

def ver_campo():
    from aplanar import VerCampo
    view = VerCampo()
    view.lift()                
    view.focus_force()        
    view.grab_set()   

def seleccion_porterias():
    from porterias import VentanaPorterias
    port = VentanaPorterias()
    port.lift()                
    port.focus_force()        
    port.grab_set()  
    
def Abrir_VAR():
    ruta = os.path.abspath("VAR.py")
    subprocess.Popen([sys.executable, ruta])

def abrir_grabaciones():
    from grabaciones import VentanaGrabaciones
    ventana = VentanaGrabaciones()
    ventana.lift()
    ventana.focus_force()
    ventana.grab_set()

def configurar_camara():
    from selector_camara import VentanaSelectCamara
    ventana = VentanaSelectCamara(callback=actualizar_indicador_camara)
    ventana.lift()
    ventana.focus_force()
    ventana.grab_set()

def actualizar_indicador_camara():
    tipo, valor = config_camara.cargar_config()
    if tipo == "ip":
        estado_camara.configure(text=" Cámara IP configurada", text_color="#00ff00")
    elif tipo == "fisica":
        estado_camara.configure(text=f" Camara Física {valor} configurada", text_color="#00ff00")
    else:
        estado_camara.configure(text=" Sin configurar", text_color="#ff6600")

def update_imagen_central(event=None):
    canvas_central.delete("all")
    w = canvas_central.winfo_width()
    h = canvas_central.winfo_height()
    resized = img_central_pil.resize((w, h), Image.Resampling.LANCZOS)
    img_central_tk = ImageTk.PhotoImage(resized)
    canvas_central.create_image(0, 0, anchor="nw", image=img_central_tk)
    canvas_central.image = img_central_tk  

def verificar_configuracion_camara():
    tipo, valor = config_camara.cargar_config()
    if tipo is None:
        from selector_camara import VentanaSelectCamara
        ventana = VentanaSelectCamara(callback=actualizar_indicador_camara)
        ventana.lift()
        ventana.focus_force()
        ventana.grab_set()


# Crear ventana principal
app = customtkinter.CTk()
app.title("Sistema VAR - RoboFut")
app.after(5000, actualizar_wifi)

app.update()
ancho = app.winfo_screenwidth()
alto = app.winfo_screenheight()
app.geometry(f"{ancho}x{alto}+0+0")
app.configure(fg_color="#1725a5")

for i in range(4):
    app.grid_columnconfigure(i, weight=1)
app.grid_rowconfigure(1, weight=3)
app.grid_rowconfigure(0, weight=1)
app.grid_rowconfigure(2, weight=1)

# Fila 0: logo - red/cmara - reloj
logo_img = customtkinter.CTkImage(light_image=Image.open(logo_path), size=(150, 150))
logo_label = customtkinter.CTkLabel(app, image=logo_img, text="")

logo_label.image = logo_img
logo_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

info_frame = customtkinter.CTkFrame(app, fg_color="transparent")
info_frame.grid(row=0, column=1, columnspan=2, sticky="nsew", padx=10)

red_label = customtkinter.CTkLabel(
    info_frame, 
    text="🛜 " + wifi(), 
    font=("Arial", 18, "bold"), 
    text_color="white"
)
red_label.pack(pady=(10, 5))

estado_camara = customtkinter.CTkLabel(
    info_frame,
    text=" Sin configurar",
    font=("Arial", 14),
    text_color="#ff6600"
)
estado_camara.pack()

reloj_label = customtkinter.CTkLabel(
    app, 
    text="", 
    font=("Arial", 20, "bold"), 
    text_color="white"
)
reloj_label.grid(row=0, column=3, sticky="e", padx=10)

# Fila 1: imagen central
img_central_pil = Image.open(imagen_central)
canvas_central = customtkinter.CTkCanvas(app, bg="white")
canvas_central.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=20, pady=20)
canvas_central.bind("<Configure>", update_imagen_central)

# Fila 2: botones principales
boton_config_camara = customtkinter.CTkButton(
    app, 
    text="⚙️ Config. Cámara", 
    command=configurar_camara, 
    width=200, 
    height=60, 
    font=("Arial", 16), 
    corner_radius=10, 
    fg_color="#4a0e4e", 
    hover_color="#6b1470", 
    text_color="white"
)

boton_seleccion = customtkinter.CTkButton(
    app, 
    text="Selección de campo", 
    command=abrir_seleccion_campo, 
    width=200, 
    height=60, 
    font=("Arial", 18), 
    corner_radius=10, 
    fg_color="#02080F", 
    hover_color="#022E51", 
    text_color="white"
)

boton_VAR = customtkinter.CTkButton(
    app, 
    text="VAR", 
    command=Abrir_VAR, 
    width=200, 
    height=60, 
    font=("Arial", 18), 
    corner_radius=10, 
    fg_color="#02080F", 
    hover_color="#022E51", 
    text_color="white"
)

boton_porterias = customtkinter.CTkButton(
    app, 
    text="Porterías", 
    command=seleccion_porterias, 
    width=200, 
    height=60, 
    font=("Arial", 18), 
    corner_radius=10, 
    fg_color="#02080F", 
    hover_color="#022E51", 
    text_color="white"
)

boton_vercampo = customtkinter.CTkButton(
    app, 
    text="Ver Campo", 
    command=ver_campo, 
    width=200, 
    height=60, 
    font=("Arial", 18), 
    corner_radius=10, 
    fg_color="#02080F", 
    hover_color="#022E51", 
    text_color="white"
)

boton_grabaciones = customtkinter.CTkButton(
    app, 
    text="Grabaciones", 
    command=abrir_grabaciones, 
    width=200, 
    height=60, 
    font=("Arial", 18), 
    corner_radius=10, 
    fg_color="#02080F", 
    hover_color="#022E51", 
    text_color="white"
)

# botones
boton_config_camara.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
boton_seleccion.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
boton_VAR.grid(row=2, column=2, padx=10, pady=10, sticky="ew")
boton_porterias.grid(row=2, column=3, padx=10, pady=10, sticky="ew")

# Fila 3: botones adicionales
boton_vercampo.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
boton_grabaciones.grid(row=3, column=2, columnspan=2, padx=10, pady=10, sticky="ew")

actualizar_reloj()

actualizar_indicador_camara()
app.after(500, verificar_configuracion_camara)

app.mainloop()
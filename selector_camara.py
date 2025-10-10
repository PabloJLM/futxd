import customtkinter
import cv2
from PIL import Image, ImageTk
import config_camara
from tkinter import messagebox

class VentanaSelectCamara(customtkinter.CTkToplevel):
    def __init__(self, master=None, callback=None):
        super().__init__(master)
        self.title("Configuración de Cámara")
        self.geometry("600x500")
        self.configure(fg_color="#1b1f2b")
        self.callback = callback
        
        # Centrar ventana
        self.after(100, self.centrar_ventana)
        

        titulo = customtkinter.CTkLabel(
            self, 
            text="Selecciona el tipo de camara",
            font=("Arial", 24, "bold"),
            text_color="white"
        )
        titulo.pack(pady=30)
        
        frame_botones = customtkinter.CTkFrame(self, fg_color="transparent")
        frame_botones.pack(pady=20)
        
        btn_ip = customtkinter.CTkButton(
            frame_botones,
            text="Cámara IP (RTSP)",
            command=self.seleccionar_ip,
            width=250,
            height=80,
            font=("Arial", 18),
            corner_radius=10,
            fg_color="#02080F",
            hover_color="#022E51"
        )
        btn_ip.pack(pady=15)
        
        btn_fisica = customtkinter.CTkButton(
            frame_botones,
            text="Cámara Física USB",
            command=self.seleccionar_fisica,
            width=250,
            height=80,
            font=("Arial", 18),
            corner_radius=10,
            fg_color="#02080F",
            hover_color="#022E51"
        )
        btn_fisica.pack(pady=15)
        
        self.frame_config = customtkinter.CTkFrame(self)
        
        self.label_ip = customtkinter.CTkLabel(
            self.frame_config,
            text="Ingresa la URL RTSP:",
            font=("Arial", 16)
        )
        
        self.entry_ip = customtkinter.CTkEntry(
            self.frame_config,
            width=450,
            height=40,
            placeholder_text="rtsp://usuario:password@192.168.1.X:554/stream2"
        )
        
        self.label_fisica = customtkinter.CTkLabel(
            self.frame_config,
            text="Selecciona el índice de la cámara:",
            font=("Arial", 16)
        )
        
        self.combo_fisica = customtkinter.CTkComboBox(
            self.frame_config,
            values=["0", "1", "2", "3"],
            width=200,
            height=40
        )
        self.combo_fisica.set("1")
        
        self.btn_probar = customtkinter.CTkButton(
            self.frame_config,
            text="Probar Conexión",
            command=self.probar_conexion,
            width=200,
            height=50,
            font=("Arial", 16),
            fg_color="#0a5f0a",
            hover_color="#0d7a0d"
        )
        
        self.btn_guardar = customtkinter.CTkButton(
            self.frame_config,
            text="Guardar y Continuar",
            command=self.guardar_config,
            width=200,
            height=50,
            font=("Arial", 16),
            fg_color="#1a5fb4",
            hover_color="#2277cc"
        )
        
        self.label_estado = customtkinter.CTkLabel(
            self,
            text="",
            font=("Arial", 14)
        )
        
        self.tipo_seleccionado = None
        self.protocol("WM_DELETE_WINDOW", self.cerrar)
    
    def centrar_ventana(self):
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
    
    def seleccionar_ip(self):
        self.tipo_seleccionado = "ip"
        self.mostrar_config_ip()
    
    def seleccionar_fisica(self):
        self.tipo_seleccionado = "fisica"
        self.mostrar_config_fisica()
    
    def mostrar_config_ip(self):
        for widget in self.frame_config.winfo_children():
            widget.pack_forget()
        
        self.label_ip.pack(pady=10)
        self.entry_ip.pack(pady=10)
        self.btn_probar.pack(pady=10)
        self.btn_guardar.pack(pady=10)
        
        self.frame_config.pack(pady=20, padx=20)
        self.label_estado.pack(pady=10)
    
    def mostrar_config_fisica(self):

        for widget in self.frame_config.winfo_children():
            widget.pack_forget()
        

        self.label_fisica.pack(pady=10)
        self.combo_fisica.pack(pady=10)
        self.btn_probar.pack(pady=10)
        self.btn_guardar.pack(pady=10)
        
        self.frame_config.pack(pady=20, padx=20)
        self.label_estado.pack(pady=10)
    
    def probar_conexion(self):
        self.label_estado.configure(text="Probando conexión...", text_color="yellow")
        self.update()
        
        if self.tipo_seleccionado == "ip":
            url = self.entry_ip.get().strip()
            if not url:
                self.label_estado.configure(text="Ingresa una URL válida", text_color="red")
                return
            
            cap = cv2.VideoCapture(url)
        else:
            indice = int(self.combo_fisica.get())
            cap = cv2.VideoCapture(indice)
        
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                self.label_estado.configure(text="Conexión exitosa", text_color="green")
                messagebox.showinfo("Éxito", "La cámara se conectó correctamente")
            else:
                self.label_estado.configure(text="No se pudo leer frame", text_color="red")
                messagebox.showerror("Error", "La cámara se conectó pero no pudo leer frames")
        else:
            self.label_estado.configure(text="Error de conexión", text_color="red")
            messagebox.showerror("Error", "No se pudo conectar a la cámara")
            cap.release()
    
    def guardar_config(self):
        if self.tipo_seleccionado == "ip":
            url = self.entry_ip.get().strip()
            if not url:
                messagebox.showwarning("Advertencia", "Ingresa una URL válida")
                return
            
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                messagebox.showerror("Error", "No se pudo conectar. Verifica la URL")
                cap.release()
                return
            cap.release()
            
            config_camara.guardar_config("ip", url)
            messagebox.showinfo("Guardado", "Configuración de cámara IP guardada")
        
        else:
            indice = int(self.combo_fisica.get())
            
            cap = cv2.VideoCapture(indice)
            if not cap.isOpened():
                messagebox.showerror("Error", f"No se pudo acceder a la cámara {indice}")
                cap.release()
                return
            cap.release()
            
            config_camara.guardar_config("fisica", indice)
            messagebox.showinfo("Guardado", f"Configuración de cámara física {indice} guardada")
        
        if self.callback:
            self.callback()
        
        self.destroy()
    
    def cerrar(self):
        self.destroy()


if __name__ == "__main__":
    app = customtkinter.CTk()
    app.withdraw()
    ventana = VentanaSelectCamara()
    app.mainloop()
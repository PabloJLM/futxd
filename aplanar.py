import customtkinter
import cv2
from PIL import Image, ImageTk
import numpy as np
import utilidades_camara

class VerCampo(customtkinter.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Campo Aplanado")
        self.geometry("900x500")
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.canvas = customtkinter.CTkCanvas(self, width=800, height=400)
        self.canvas.pack(padx=10, pady=10, fill="both", expand=True)
        self.after(100, self.centrar_ventana)

    def centrar_ventana(self):
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

        try:
            pts_src = np.load("esquinas.npy")
        except Exception as e:
            print(f"Error al cargar 'esquinas.npy': {e}")
            self.destroy()
            return

        width, height = 800, 400
        pts_dst = np.float32([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ])

        self.M = cv2.getPerspectiveTransform(pts_src, pts_dst)
        self.width, self.height = width, height

        # Usar la función helper para obtener la cámara
        self.cap = utilidades_camara.obtener_captura()
        if self.cap is None:
            self.destroy()
            return

        self.after(30, self.actualizar_frame)

    def actualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.after(100, self.actualizar_frame)
            return

        warped = cv2.warpPerspective(frame, self.M, (self.width, self.height))
        frame_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((self.canvas.winfo_width(), self.canvas.winfo_height()))
        self.img_tk = ImageTk.PhotoImage(img)

        self.canvas.create_image(0, 0, anchor="nw", image=self.img_tk)
        self.after(30, self.actualizar_frame)

    def cerrar(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.destroy()
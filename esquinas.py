import customtkinter
import cv2
from PIL import Image, ImageTk
import numpy as np
import utilidades_camara

puntos = []

class VentanaEsquinas(customtkinter.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Seleccionar Esquinas")
        self.geometry("900x600")
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.canvas = customtkinter.CTkCanvas(self, width=800, height=500)
        self.canvas.pack(padx=10, pady=10, fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.after(100, self.centrar_ventana)

    def centrar_ventana(self):
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

        self.puntos = []
        
        self.cap = utilidades_camara.obtener_captura()
        if self.cap is None:
            self.destroy()
            return

        self.guia = cv2.imread("guia.png")
        if self.guia is not None:
            self.guia = cv2.resize(self.guia, (300, 250))
        else:
            print("No se pudo cargar la guía 'guia.png'")

        self.actualizar_frame()

    def actualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.after(100, self.actualizar_frame)
            return

        if self.guia is not None:
            h_guia, w_guia = self.guia.shape[:2]
            h_frame, w_frame = frame.shape[:2]
            cx, cy = w_frame // 2 - w_guia // 2, h_frame // 2 - h_guia // 2

            roi = frame[cy:cy + h_guia, cx:cx + w_guia]
            guia_gray = cv2.cvtColor(self.guia, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(guia_gray, 1, 255, cv2.THRESH_BINARY)
            bg = cv2.bitwise_and(roi, roi, mask=cv2.bitwise_not(mask))
            fg = cv2.bitwise_and(self.guia, self.guia, mask=mask)
            frame[cy:cy + h_guia, cx:cx + w_guia] = cv2.add(bg, fg)

        for p in self.puntos:
            cv2.circle(frame, p, 6, (0, 255, 0), -1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_w, img_h = img.size

        scale = min(canvas_w / img_w, canvas_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        fondo = Image.new("RGB", (canvas_w, canvas_h), (0, 0, 0))
        offset_x = (canvas_w - new_w) // 2
        offset_y = (canvas_h - new_h) // 2
        fondo.paste(img, (offset_x, offset_y))

        self.img_tk = ImageTk.PhotoImage(fondo)
        self.canvas.create_image(0, 0, anchor="nw", image=self.img_tk)

        self.after(30, self.actualizar_frame)

    def on_click(self, event):
        if len(self.puntos) >= 4:
            return

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        ret, frame = self.cap.read()
        if not ret:
            return

        img_h, img_w = frame.shape[:2]
        scale = min(canvas_w / img_w, canvas_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        offset_x = (canvas_w - new_w) // 2
        offset_y = (canvas_h - new_h) // 2

        if offset_x <= event.x <= offset_x + new_w and offset_y <= event.y <= offset_y + new_h:
            x = int((event.x - offset_x) / scale)
            y = int((event.y - offset_y) / scale)
            self.puntos.append((x, y))
            print(f"Punto {len(self.puntos)}: ({x}, {y})")

            if len(self.puntos) == 4:
                np.save("esquinas.npy", np.array(self.puntos, dtype=np.float32))
                print("Esquinas guardadas en 'esquinas.npy'")
                self.cerrar()

    def cerrar(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.destroy()
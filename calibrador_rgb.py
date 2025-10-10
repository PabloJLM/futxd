import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image, ImageTk
import utilidades_camara

class Principal:
    def __init__(self, root):
        self.root = root
        self.root.title("Calibrador de RGB (con limpieza HSV)")

        self.frame_width = 640
        self.frame_height = 480

        self.sliders = {}
        self.labels = {}
        self.entries = {}

        values = {
            "R Min": (0, 255),
            "R Max": (0, 255),
            "G Min": (0, 255),
            "G Max": (0, 255),
            "B Min": (0, 255),
            "B Max": (0, 255)
        }

        slider_frame = ctk.CTkFrame(root)
        slider_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        for i, (name, (min_val, max_val)) in enumerate(values.items()):
            ctk.CTkLabel(slider_frame, text=name).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            self.sliders[name] = ctk.CTkSlider(slider_frame, from_=min_val, to=max_val, command=self.update_values)
            self.sliders[name].grid(row=i, column=1, padx=5, pady=5)
            self.labels[name] = ctk.CTkLabel(slider_frame, text=f"{int(self.sliders[name].get())}")
            self.labels[name].grid(row=i, column=2, padx=5, pady=5)

            self.entries[name] = ctk.CTkEntry(slider_frame, width=50)
            self.entries[name].grid(row=i, column=3, padx=5, pady=5)
            self.entries[name].insert(0, str(int(self.sliders[name].get())))
            self.entries[name].bind("<Return>", self.update_from_entry)

        self.sliders["R Min"].set(0)
        self.sliders["R Max"].set(255)
        self.sliders["G Min"].set(0)
        self.sliders["G Max"].set(255)
        self.sliders["B Min"].set(0)
        self.sliders["B Max"].set(255)

        self.image_label = ctk.CTkLabel(root, text="")
        self.image_label.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.cap = utilidades_camara.obtener_captura()
        if self.cap is None:
            print("Error: No se pudo conectar a la cámara")
            self.root.quit()
            return

        self.root.bind("<Configure>", self.resize_window)
        self.update_frame()

    def resize_window(self, event=None):
        self.frame_width = self.root.winfo_width() - 20
        self.frame_height = self.root.winfo_height() - 50

    def update_values(self, _=None):
        for name in self.labels:
            val = int(self.sliders[name].get())
            self.labels[name].configure(text=f"{val}")
            self.entries[name].delete(0, ctk.END)
            self.entries[name].insert(0, str(val))

    def update_from_entry(self, event):
        for name in self.entries:
            try:
                val = int(self.entries[name].get())
                val = max(0, min(val, 255))
                self.sliders[name].set(val)
            except ValueError:
                pass

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (self.frame_width, self.frame_height))

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            low_hsv = np.array([0, 76, 90])
            up_hsv = np.array([179, 255, 255])
            mask_hsv = cv2.inRange(hsv, low_hsv, up_hsv)
            result_hsv = cv2.bitwise_and(frame, frame, mask=mask_hsv)

            blurred = cv2.GaussianBlur(result_hsv, (9, 9), 0)
            kernel = np.ones((5, 5), np.uint8)
            limpieza = cv2.morphologyEx(blurred, cv2.MORPH_OPEN, kernel)

            limpieza_rgb = cv2.cvtColor(limpieza, cv2.COLOR_BGR2RGB)

            lower_rgb = np.array([
                int(self.sliders["R Min"].get()),
                int(self.sliders["G Min"].get()),
                int(self.sliders["B Min"].get())])

            upper_rgb = np.array([
                int(self.sliders["R Max"].get()),
                int(self.sliders["G Max"].get()),
                int(self.sliders["B Max"].get())])

            mask_rgb = cv2.inRange(limpieza_rgb, lower_rgb, upper_rgb)
            result_rgb = cv2.bitwise_and(limpieza_rgb, limpieza_rgb, mask=mask_rgb)

            img = Image.fromarray(result_rgb)
            img = ImageTk.PhotoImage(img)
            self.image_label.configure(image=img)
            self.image_label.image = img

        self.root.after(10, self.update_frame)

    def run(self):
        self.root.mainloop()
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.geometry("800x600")
    root.attributes('-fullscreen', False)
    app = Principal(root)
    app.run()
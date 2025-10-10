import cv2
import config_camara
from tkinter import messagebox

def obtener_captura():
    tipo, valor = config_camara.cargar_config()
    
    if tipo is None:
        messagebox.showerror(
            "Error de Configuración",
            "No se ha configurado ninguna cámara.\nPor favor, configura una cámara desde el menú principal."
        )
        return None
    
    if tipo == "ip":
        print(f"Conectando a cámara IP: {valor}")
        cap = cv2.VideoCapture(valor)
    elif tipo == "fisica":
        print(f"Conectando a cámara física: {valor}")
        cap = cv2.VideoCapture(int(valor))
    else:
        return None
    
    if not cap.isOpened():
        messagebox.showerror(
            "Error de Conexión",
            f"No se pudo conectar a la cámara.\nTipo: {tipo}\nValor: {valor}"
        )
        return None
    
    return cap

def verificar_conexion():
    tipo, valor = config_camara.cargar_config()
    return tipo is not None
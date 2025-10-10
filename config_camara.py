import json
import os

CONFIG_FILE = "camera_config.json"

def guardar_config(tipo_camara, valor):
    config = {
        "tipo": tipo_camara,
        "valor": valor
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
    print(f"Configuración guardada: {config}")

def cargar_config():
    if not os.path.exists(CONFIG_FILE):
        return None, None
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config.get("tipo"), config.get("valor")
    except:
        return None, None

def obtener_video_source():
    tipo, valor = cargar_config()
    
    if tipo == "ip":
        return valor
    elif tipo == "fisica":
        return int(valor)
    else:
        return None
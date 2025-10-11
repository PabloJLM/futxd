import cv2
import numpy as np
from collections import deque
import pygame
import os
import datetime
import config_camara

WIDTH, HEIGHT = 800, 400
FPS = 25
DURACION = 10
FRAMES_UMBRAL = FPS * DURACION
FRAMES_EXTRA = 3 * FPS

pygame.mixer.init()
pygame.mixer.music.load("gol.mp3")

def reproducir_sonido():
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.play()

def cruzo_linea(p_actual, p_anterior, p1, p2):
    def ccw(A, B, C):
        return (C[1]-A[1])*(B[0]-A[0]) > (B[1]-A[1])*(C[0]-A[0])
    return (ccw(p_anterior, p1, p2) != ccw(p_actual, p1, p2)) and (ccw(p_anterior, p_actual, p1) != ccw(p_anterior, p_actual, p2))

def detectar_pelota(frame_aplanado, kernel, debug=False):
    hsv = cv2.cvtColor(frame_aplanado, cv2.COLOR_BGR2HSV)
    lower = np.array([0, 0, 200], dtype=np.uint8)
    upper = np.array([179, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.GaussianBlur(mask, (7, 7), 0)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if debug:
        mask_vis = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    else:
        mask_vis = mask
    for cnt in sorted(contours, key=cv2.contourArea, reverse=True):
        area = cv2.contourArea(cnt)
        if area < 300:
            continue
        perim = cv2.arcLength(cnt, True)
        if perim == 0:
            continue
        circularidad = 4 * np.pi * (area / (perim ** 2 + 1e-6))
        if circularidad > 0.6:
            (x, y), radio = cv2.minEnclosingCircle(cnt)
            centro = (int(x), int(y))
            if debug:
                cv2.drawContours(mask_vis, [cnt], -1, (0,255,0), 2)
                cv2.circle(mask_vis, centro, int(radio), (0,0,255), 2)
            return centro, int(radio), mask_vis
    return None, 0, mask_vis

def obtener_video_source():
    tipo, valor = config_camara.cargar_config()
    if tipo == "ip":
        return valor
    elif tipo == "fisica":
        return int(valor)
    else:
        print("ERROR: No hay configuración de cámara. Por favor, configura una cámara desde el menú principal.")
        return None

def reconectar_camara(video_source):
    print("Reintentando conexión a la cámara...")
    return cv2.VideoCapture(video_source)

def main():
    os.makedirs("var", exist_ok=True)
    video_source = obtener_video_source()
    if video_source is None:
        return
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return
    kernel = np.ones((5, 5), np.uint8)
    buffer_frames = deque(maxlen=FRAMES_UMBRAL)
    try:
        pts_src = np.load("esquinas.npy")
        porterias = np.load("porterias.npy", allow_pickle=True).item()
    except Exception as e:
        print("Error cargando archivos:", e)
        return
    pts_dst = np.float32([[0, 0], [WIDTH-1, 0], [WIDTH-1, HEIGHT-1], [0, HEIGHT-1]])
    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    p1_A, p2_A = map(tuple, porterias["porteria_A"])
    p1_B, p2_B = map(tuple, porterias["porteria_B"])
    contador_A = contador_B = 1
    ultimo_gol_A = ultimo_gol_B = -FRAMES_UMBRAL
    post_gol_restante_A = post_gol_restante_B = 0
    frames_post_A = []
    frames_post_B = []
    kalman = cv2.KalmanFilter(4, 2)
    kalman.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
    kalman.transitionMatrix = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]], np.float32)
    kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
    kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.5
    kalman.statePost = np.array([[0.],[0.],[0.],[0.]], dtype=np.float32)
    detectado = False
    pelota_anterior = None
    estela = deque(maxlen=20)
    frame_actual = 0
    errores_lectura = 0
    cv2.namedWindow("VAR", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("VAR", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("VAR", cv2.WND_PROP_TOPMOST, 1)
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                errores_lectura += 1
                if errores_lectura > 50:
                    cap.release()
                    cap = reconectar_camara(video_source)
                    errores_lectura = 0
                continue
            errores_lectura = 0
            frame_aplanado = cv2.warpPerspective(frame, M, (WIDTH, HEIGHT))
            cv2.line(frame_aplanado, p1_A, p2_A, (0, 255, 0), 2)
            cv2.line(frame_aplanado, p1_B, p2_B, (255, 0, 0), 2)
            centro, radio, mask_clean = detectar_pelota(frame_aplanado, kernel, debug=True)
            prediccion = kalman.predict()
            pred_x, pred_y = int(prediccion[0,0]), int(prediccion[1,0])
            pelota_actual = (pred_x, pred_y)
            if centro is not None:
                medida = np.array([[np.float32(centro[0])],[np.float32(centro[1])]])
                kalman.correct(medida)
                cv2.circle(frame_aplanado, centro, max(5, radio), (0,255,0), 2)
                detectado = True
            else:
                detectado = False
                cv2.circle(frame_aplanado, pelota_actual, 6, (0,0,255), -1)
            pos_para_estela = centro if centro is not None else pelota_actual
            estela.appendleft(pos_para_estela)
            for i in range(1, len(estela)):
                if estela[i-1] is not None and estela[i] is not None:
                    cv2.line(frame_aplanado, estela[i-1], estela[i], (0,255,255), 2)
            if pelota_anterior:
                if cruzo_linea(pelota_actual, pelota_anterior, p1_A, p2_A) and frame_actual - ultimo_gol_A >= FRAMES_UMBRAL:
                    reproducir_sonido()
                    post_gol_restante_A = FRAMES_EXTRA
                    ultimo_gol_A = frame_actual
                    contador_A += 1
                if cruzo_linea(pelota_actual, pelota_anterior, p1_B, p2_B) and frame_actual - ultimo_gol_B >= FRAMES_UMBRAL:
                    reproducir_sonido()
                    post_gol_restante_B = FRAMES_EXTRA
                    ultimo_gol_B = frame_actual
                    contador_B += 1
            pelota_anterior = pelota_actual
            buffer_frames.append(frame_aplanado.copy())
            if post_gol_restante_A > 0:
                frames_post_A.append(frame_aplanado.copy())
                post_gol_restante_A -= 1
                if post_gol_restante_A == 0:
                    try:
                        ahora = datetime.datetime.now().strftime("%H-%M-%S")
                        nombre = f"var/grabacionA_{ahora}.mp4"
                        out = cv2.VideoWriter(nombre, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (WIDTH, HEIGHT))
                        for f in buffer_frames:
                            out.write(f)
                        for f in frames_post_A:
                            out.write(f)
                        out.release()
                        print(f"Grabado gol A: {nombre}")
                    finally:
                        frames_post_A.clear()
            if post_gol_restante_B > 0:
                frames_post_B.append(frame_aplanado.copy())
                post_gol_restante_B -= 1
                if post_gol_restante_B == 0:
                    try:
                        ahora = datetime.datetime.now().strftime("%H-%M-%S")
                        nombre = f"var/grabacionB_{ahora}.mp4"
                        out = cv2.VideoWriter(nombre, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (WIDTH, HEIGHT))
                        for f in buffer_frames:
                            out.write(f)
                        for f in frames_post_B:
                            out.write(f)
                        out.release()
                        print(f"Grabado gol B: {nombre}")
                    finally:
                        frames_post_B.clear()
            cv2.imshow("VAR", frame_aplanado)
            cv2.imshow("Mask", mask_clean)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                break
            frame_actual += 1
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

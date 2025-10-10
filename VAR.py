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

def detectar_pelota(frame_aplanado, kernel):
    hsv = cv2.cvtColor(frame_aplanado, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, (0, 76, 90), (179, 255, 255))
    masked1 = cv2.bitwise_and(frame_aplanado, frame_aplanado, mask=mask1)
    mask2 = cv2.inRange(masked1, (0, 0, 80), (140, 255, 255))
    blur = cv2.GaussianBlur(mask2, (9, 9), 0)
    clean = cv2.morphologyEx(blur, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in sorted(contours, key=cv2.contourArea, reverse=True):
        area = cv2.contourArea(cnt)
        if area < 250: continue
        perim = cv2.arcLength(cnt, True)
        if perim == 0: continue
        circularidad = 4 * np.pi * (area / (perim ** 2))
        if circularidad > 0.87:
            (x, y), radio = cv2.minEnclosingCircle(cnt)
            return (int(x), int(y)), int(radio), clean
    return None, 0, clean

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
    kalman.measurementMatrix = np.array([[1,0,0,0], [0,1,0,0]], np.float32)
    kalman.transitionMatrix = np.array([[1,0,1,0], [0,1,0,1], [0,0,1,0], [0,0,0,1]], np.float32)
    kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

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
                print(f"Error leyendo frame ({errores_lectura})")
                if errores_lectura > 50:
                    cap.release()
                    cap = reconectar_camara(video_source)
                    errores_lectura = 0
                continue
            errores_lectura = 0

            frame_aplanado = cv2.warpPerspective(frame, M, (WIDTH, HEIGHT))
            cv2.line(frame_aplanado, p1_A, p2_A, (0, 255, 0), 2)
            cv2.line(frame_aplanado, p1_B, p2_B, (255, 0, 0), 2)

            centro, radio, mask_clean = detectar_pelota(frame_aplanado, kernel)

            if centro:
                medida = np.array([[np.float32(centro[0])], [np.float32(centro[1])]])
                kalman.correct(medida)
                detectado = True
            else:
                detectado = False

            prediccion = kalman.predict()
            pred_x, pred_y = int(prediccion[0, 0]), int(prediccion[1, 0])

            pelota_actual = (pred_x, pred_y)

            if detectado:
                cv2.circle(frame_aplanado, pelota_actual, 10, (0, 0, 255), -1)
                estela.appendleft(pelota_actual)
            else:
                estela.appendleft(None)
            for i in range(1, len(estela)):
                if estela[i - 1] is not None and estela[i] is not None:
                    cv2.line(frame_aplanado, estela[i - 1], estela[i], (0, 255, 255), 2)

            if pelota_anterior:
                if cruzo_linea(pelota_actual, pelota_anterior, p1_A, p2_A) and frame_actual - ultimo_gol_A >= FRAMES_UMBRAL:
                    print("¡GOL en Portería A!")
                    reproducir_sonido()
                    post_gol_restante_A = FRAMES_EXTRA
                    ultimo_gol_A = frame_actual
                    contador_A += 1

                if cruzo_linea(pelota_actual, pelota_anterior, p1_B, p2_B) and frame_actual - ultimo_gol_B >= FRAMES_UMBRAL:
                    print("¡GOL en Portería B!")
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

            try:
               # cv2.putText(frame_aplanado, f"Goles A: {contador_A-1}", (10, 50),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
               # cv2.putText(frame_aplanado, f"Goles B: {contador_B-1}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                cv2.imshow("VAR", frame_aplanado)
                #cv2.imshow("Pelota Limpia", mask_clean)
            except cv2.error as e:
                print("Error en imshow:", e)
                break

            frame_actual += 1
            if cv2.waitKey(1) & 0xFF == ord('q') or cv2.waitKey(1) & 0xFF == ord('Q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
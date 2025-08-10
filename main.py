import cv2
import mediapipe as mp
import time
import os
import numpy as np

from database_setup import criar_banco_de_dados
# Vou supor que você já tem o database_setup.py e o core_functions.py com o banco pronto.

criar_banco_de_dados()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
rostos_dir = os.path.join(BASE_DIR, 'rostos_cadastrados')
capturas_dir = os.path.join(BASE_DIR, 'capturas_log')

if not os.path.exists(rostos_dir):
    os.makedirs(rostos_dir)
if not os.path.exists(capturas_dir):
    os.makedirs(capturas_dir)

video_capture = cv2.VideoCapture(0)  # ou IP webcam

mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

INTERVALO_VERIFICACAO = 3.0
ultimo_tempo_verificacao = 0

print("\n[INFO] Sistema de reconhecimento facial contínuo iniciado.")
print("Pressione 'Q' na janela da câmera para sair.")

def verificar_pessoa(rosto_img):
    """
    Função simples que compara o rosto capturado com imagens cadastradas,
    retornando o nome da pessoa se encontrar similaridade acima do limiar.
    """

    def calcular_histograma(img):
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([img_hsv], [0,1], None, [50,60], [0,180,0,256])
        cv2.normalize(hist, hist)
        return hist

    hist_rosto = calcular_histograma(rosto_img)

    melhor_nome = None
    melhor_score = 0
    LIMIAR_SIMILARIDADE = 0.5  # Ajuste conforme seu teste

    for arquivo in os.listdir(rostos_dir):
        caminho_img = os.path.join(rostos_dir, arquivo)
        img_cadastrada = cv2.imread(caminho_img)
        if img_cadastrada is None:
            continue

        hist_cadastrada = calcular_histograma(img_cadastrada)
        score = cv2.compareHist(hist_rosto, hist_cadastrada, cv2.HISTCMP_CORREL)

        if score > melhor_score and score > LIMIAR_SIMILARIDADE:
            melhor_score = score
            melhor_nome = os.path.splitext(arquivo)[0]  # nome do arquivo sem extensão

    return melhor_nome

with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6) as face_detection:
    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("[ERRO] Não foi possível capturar frame da câmera. Tentando novamente...")
            time.sleep(2)
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)

        rosto_detectado_na_frame = bool(results.detections)
        if rosto_detectado_na_frame:
            for detection in results.detections:
                mp_drawing.draw_detection(frame, detection)

        cv2.imshow('Sistema de Reconhecimento Facial - Pressione Q para Sair', frame)

        tempo_atual = time.time()
        if rosto_detectado_na_frame and (tempo_atual - ultimo_tempo_verificacao > INTERVALO_VERIFICACAO):
            print("\n[INFO] Rosto detectado. Iniciando verificação...")

            detection = results.detections[0]
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = frame.shape
            x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(iw, x + w), min(ih, y + h)

            rosto_img_recortado = frame[y1:y2, x1:x2]

            if rosto_img_recortado.size != 0:
                resultado = verificar_pessoa(rosto_img_recortado)
                if resultado:
                    print(f"[INFO] Rosto reconhecido no banco: {resultado}")
                    cv2.putText(frame, f"Reconhecido: {resultado}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    print("[INFO] Rosto NÃO reconhecido no banco.")
                    cv2.putText(frame, "Nao reconhecido", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            ultimo_tempo_verificacao = tempo_atual

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

print("\n[INFO] Encerrando o sistema...")
video_capture.release()
cv2.destroyAllWindows()
print("[INFO] Sistema finalizado.")

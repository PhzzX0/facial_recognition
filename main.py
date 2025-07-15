# Importa as bibliotecas necessárias para visão computacional, tempo e sistema de arquivos

# Importa a biblioteca OpenCV para captura de vídeo e manipulação de imagens (usada em todo o processamento de vídeo)
import cv2
# Importa a biblioteca MediaPipe para detecção facial em tempo real (usada para detectar rostos no vídeo)
import mediapipe as mp
# Importa a biblioteca de tempo para medir intervalos entre verificações (usada para limitar a frequência de análise)
import time
# Importa a biblioteca OS para manipulação de caminhos de arquivos e diretórios (usada para salvar capturas e organizar pastas)
import os

# Importa funções internas do sistema

# Importa a função que cria o banco de dados e tabelas, garantindo que tudo esteja pronto antes de rodar o sistema
from database_setup import criar_banco_de_dados
# Importa a função que realiza a verificação facial comparando com dados existentes no banco
from core_functions import *

# Garante que o banco de dados e tabelas sejam criados ao iniciar
criar_banco_de_dados()

# Define caminhos das pastas principais
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
rostos_dir = os.path.join(BASE_DIR, 'rostos_cadastrados')
capturas_dir = os.path.join(BASE_DIR, 'capturas_log')

# Cria as pastas se não existirem
if not os.path.exists(rostos_dir):
    os.makedirs(rostos_dir)
if not os.path.exists(capturas_dir):
    os.makedirs(capturas_dir)

# Abre o stream de vídeo do IP Webcam (mude a URL conforme seu IP)
video_capture = cv2.VideoCapture(0)#'http://192.168.0.0:8080/video')

# Inicializa os módulos do MediaPipe
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Define o intervalo entre verificações faciais
INTERVALO_VERIFICACAO = 3.0
ultimo_tempo_verificacao = 0

# Mensagens iniciais no terminal
print("\n[INFO] Sistema de reconhecimento facial contínuo iniciado.")
print("Pressione 'Q' na janela da câmera para sair.")

# Inicia o loop principal com detecção facial ativa
with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6) as face_detection:
    while True:
        # Captura um frame do vídeo
        ret, frame = video_capture.read()
        if not ret:
            print("[ERRO] Não foi possível capturar frame da câmera. Tentando novamente...")
            time.sleep(2)
            continue

        # Converte a imagem para RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)

        # Verifica se algum rosto foi detectado
        rosto_detectado_na_frame = bool(results.detections)
        if rosto_detectado_na_frame:
            for detection in results.detections:
                mp_drawing.draw_detection(frame, detection)

        # Exibe o vídeo com deteções
        cv2.imshow('Sistema de Reconhecimento Facial - Pressione Q para Sair', frame)

        # Verificação automática após intervalo
        tempo_atual = time.time()
        if rosto_detectado_na_frame and (tempo_atual - ultimo_tempo_verificacao > INTERVALO_VERIFICACAO):
            print("\n[INFO] Rosto detectado. Iniciando verificação...")

            # Extrai coordenadas da caixa delimitadora do rosto
            detection = results.detections[0]
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = frame.shape
            x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(iw, x + w), min(ih, y + h)

            # Recorta o rosto da imagem
            rosto_img_recortado = frame[y1:y2, x1:x2]

            # Se a imagem for válida, chama a verificação
            if rosto_img_recortado.size != 0:
                verificar_pessoa(rosto_img_recortado)

            # Atualiza o tempo da última verificação
            ultimo_tempo_verificacao = tempo_atual

        # Encerra o loop se 'q' for pressionado
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Libera recursos após o fim do programa
print("\n[INFO] Encerrando o sistema...")
video_capture.release()
cv2.destroyAllWindows()
print("[INFO] Sistema finalizado.")
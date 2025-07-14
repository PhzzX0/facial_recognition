# Importa bibliotecas necessárias para banco de dados, manipulação de arquivos e visão computacional

# Importa a biblioteca sqlite3 para interagir com o banco de dados SQLite (usada nos logs e verificações de usuários)
import sqlite3
# Importa a biblioteca OS para manipulação de caminhos de arquivos e diretórios (usada para salvar capturas e organizar pastas)
import os
# Importa a biblioteca OpenCV para captura de vídeo e manipulação de imagens (usada em todo o processamento de vídeo)
import cv2
# Importa a função datetime para gerar timestamps com data e hora atual (usada em logs e nomes de arquivos)
from datetime import datetime
# Importa a biblioteca DeepFace para fazer a verificação facial entre duas imagens (usada na comparação de rostos)
from deepface import DeepFace

# --- CONFIGURAÇÕES ---
# Define diretório base onde está o arquivo atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Caminho completo do banco de dados SQLite
db_path = os.path.join(BASE_DIR, 'database.db')
# Caminho onde as imagens de rosto capturadas serão salvas
capturas_dir = os.path.join(BASE_DIR, 'capturas_log')

# Cria o diretório de capturas se ele ainda não existir
if not os.path.exists(capturas_dir):
    os.makedirs(capturas_dir)

def registrar_log_acesso(status, usuario_id=None, caminho_foto_capturada=None):
    """
    Insere um log na tabela LogsAcesso com timestamp e status da verificação.
    Pode receber o ID do usuário e o caminho da imagem capturada.
    """
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Gera um timestamp no formato "YYYY-MM-DD HH:MM:SS"
    timestamp_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Insere o log de acesso na tabela LogsAcesso
        c.execute('''
            INSERT INTO LogsAcesso (timestamp_acesso, status, usuario_id, caminho_foto_capturada)
            VALUES (?, ?, ?, ?)
        ''', (timestamp_local, status, usuario_id, caminho_foto_capturada))
        conn.commit()
        print(f"[LOG] Evento de acesso '{status}' registrado às {timestamp_local}.")
    except Exception as e:
        # Caso ocorra erro na tentativa de inserir o log
        print(f"[ERRO DE LOG] Não foi possível registrar o acesso: {e}")
    finally:
        # Fecha a conexão com o banco de dados
        conn.close()

def verificar_pessoa(imagem_rosto_detectado):
    """
    Compara rosto detectado com todos os rostos cadastrados no banco.
    Se for identificado, registra como 'Aceito' ou 'Negado'; caso contrário, 'Não Encontrado'.
    """
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Gera um nome único para a imagem capturada usando o timestamp atual
    timestamp = int(datetime.now().timestamp())
    log_img_filename = f"captura_{timestamp}.jpg"
    log_img_path = os.path.join(capturas_dir, log_img_filename)

    # Salva a imagem capturada na pasta de logs
    cv2.imwrite(log_img_path, imagem_rosto_detectado)

    try:
        # Recupera todos os usuários cadastrados no banco
        c.execute("SELECT id, nome_completo, tipo, situacao, caminho_foto_rosto FROM Usuarios")
        registros = c.fetchall()

        # Se não houver usuários cadastrados, registra como "Não Encontrado"
        if not registros:
            print("[AVISO] Nenhum usuário cadastrado para verificação.")
            registrar_log_acesso('Não Encontrado', caminho_foto_capturada=log_img_path)
            return

        pessoa_encontrada = False

        # Percorre todos os usuários cadastrados
        for user_id, nome, tipo_usuario, situacao, arquivo_rosto_db in registros:
            # Pula se a imagem do rosto do usuário não existir
            if not os.path.exists(arquivo_rosto_db):
                continue

            try:
                # Compara o rosto capturado com o rosto do banco usando DeepFace
                result = DeepFace.verify(
                    img1_path=log_img_path,
                    img2_path=arquivo_rosto_db,
                    model_name='Facenet512',
                    enforce_detection=False
                )

                # Se for verificado como verdadeiro, analisa a situação do usuário
                if result['verified']:
                    pessoa_encontrada = True
                    print("-" * 30)

                    if situacao == 'Suspenso':
                        # Usuário reconhecido mas com acesso suspenso
                        print(f"❌ ACESSO NEGADO: {nome}")
                        print(f"   - Motivo: Usuário com situação '{situacao}'")
                        registrar_log_acesso('Negado', user_id, log_img_path)
                    else:
                        # Usuário reconhecido com acesso liberado
                        print(f"✅ ACESSO ACEITO: {nome}")
                        print(f"   - Tipo: {tipo_usuario}")
                        print(f"   - Situação: {situacao}")
                        registrar_log_acesso('Aceito', user_id, log_img_path)
                    print("-" * 30)
                    return  # Finaliza após primeira correspondência

            except Exception as e:
                # Se a comparação falhar para esse usuário, exibe erro mas continua tentando os próximos
                print(f"[ERRO] Verificação falhou para {nome}. Detalhe: {e}")

        # Se nenhum rosto for compatível com os cadastrados
        if not pessoa_encontrada:
            print("❌ Pessoa não reconhecida no banco de dados.")
            registrar_log_acesso('Não Encontrado', caminho_foto_capturada=log_img_path)

    finally:
        # Encerra a conexão com o banco, independente do resultado
        conn.close()
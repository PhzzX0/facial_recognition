import sqlite3
import os
import cv2
from datetime import datetime
from deepface import DeepFace
# from catraca import enviar_comando (tira o comentário se quiser rodar o esp plmds)

# --- CONFIGURAÇÕES GLOBAIS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'database.db')
capturas_dir = os.path.join(BASE_DIR, 'capturas_log')
rostos_dir = os.path.join(BASE_DIR, 'rostos_cadastrados') 

os.makedirs(capturas_dir, exist_ok=True)
os.makedirs(rostos_dir, exist_ok=True)

# --- FUNÇÕES DE LOG E VERIFICAÇÃO FACIAL ---

def registrar_log_acesso(status, usuario_id=None, caminho_foto_capturada=None):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    timestamp_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        c.execute('''
            INSERT INTO app_LogsAcesso (timestamp_acesso, status, usuario_id, caminho_foto_capturada)
            VALUES (?, ?, ?, ?)
        ''', (timestamp_local, status, usuario_id, caminho_foto_capturada))
        conn.commit()
    finally:
        conn.close()

def verificar_pessoa(imagem_rosto_detectado):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    timestamp = int(datetime.now().timestamp())
    log_img_filename = f"captura_{timestamp}.jpg"
    log_img_path = os.path.join(capturas_dir, log_img_filename)
    cv2.imwrite(log_img_path, imagem_rosto_detectado)

    try:
        c.execute("SELECT id, nome_completo, caminho_foto_rosto FROM app_Usuarios")
        registros = c.fetchall()

        if not registros:
            registrar_log_acesso('Não Encontrado', caminho_foto_capturada=log_img_path)
            return {"resposta": 1}
        
        for user_id, nome, caminho_relativo_db in registros:
            caminho_absoluto_rosto = os.path.join(BASE_DIR, caminho_relativo_db)
            
            if not os.path.exists(caminho_absoluto_rosto):
                continue
            
            try:
                result = DeepFace.verify(img1_path=log_img_path, img2_path=caminho_absoluto_rosto, model_name='Facenet512', enforce_detection=False)
                
                if result['verified']:
                    # Busca os detalhes completos do utilizador reconhecido
                    c.execute("""
                        SELECT U.nome_completo, U.matricula, U.tipo, U.situacao, T.nome_turma, C.nome_curso
                        FROM app_Usuarios U
                        LEFT JOIN app_UsuarioTurma UT ON U.id = UT.usuario_id
                        LEFT JOIN app_Turmas T ON UT.turma_id = T.id
                        LEFT JOIN app_Cursos C ON T.curso_id = C.id
                        WHERE U.id = ?
                    """, (user_id,))
                    detalhes = c.fetchone()
                    
                    if detalhes:
                        nome_completo, matricula, tipo, situacao, turma, curso = detalhes

                        print("-" * 30)
                        if situacao == 'Suspenso':
                            print(f"ACESSO NEGADO: {nome_completo}")
                            print(f"  - Motivo: Utilizador com situação '{situacao}'")
                            registrar_log_acesso('Negado', user_id, log_img_path)
                        else:
                            # CORREÇÃO: Adicionados os prints de detalhes
                            print(f"ACESSO ACEITO: {nome_completo}")
                            print(f"  - Matrícula: {matricula or 'N/A'}")
                            print(f"  - Tipo: {tipo}")
                            print(f"  - Situação: {situacao}")
                            if tipo == 'Discente':
                                print(f"  - Curso: {curso or 'Não vinculado'}")
                                print(f"  - Turma: {turma or 'Não vinculada'}")
                            registrar_log_acesso('Aceito', user_id, log_img_path)
                            # enviar_comando('1') (tira o comentário se quiser rodar o esp plmds)
                            return {"resposta": 2, "dados": {"nome": nome_completo,
                                                             "matricula": matricula,
                                                             "tipo": tipo,
                                                             "situacao": situacao}}
                        print("-" * 30)
                            
                        return
            except Exception as e:
                print(f"Verificação falhou para {nome}. Detalhe: {e}")

        print("Pessoa não reconhecida no banco de dados.")
        return {"resposta": 1}
        registrar_log_acesso('Não Encontrado', caminho_foto_capturada=log_img_path)
    finally:
        conn.close()

# --- FUNÇÕES DE GESTÃO DE UTILIZADORES ---

def cadastrar_usuario(nome, matricula, tipo, nome_ficheiro_foto):
    caminho_relativo = os.path.join('rostos_cadastrados', nome_ficheiro_foto)
    caminho_absoluto_verificacao = os.path.join(BASE_DIR, caminho_relativo)
    if not os.path.exists(caminho_absoluto_verificacao):
        print(f"[ERRO] A foto '{nome_ficheiro_foto}' não foi encontrada na pasta 'rostos_cadastrados'.")
        return None

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO app_Usuarios (nome_completo, matricula, tipo, caminho_foto_rosto)
            VALUES (?, ?, ?, ?)
        ''', (nome, matricula, tipo, caminho_relativo))
        conn.commit()
        novo_id = c.lastrowid
        print(f"[INFO] Utilizador '{nome}' cadastrado com sucesso.")
        return novo_id
    except sqlite3.IntegrityError:
        print(f"[ERRO] Matrícula '{matricula}' já existe.")
        return None
    finally:
        conn.close()

def excluir_usuario(usuario_nome_completo):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("SELECT caminho_foto_rosto FROM app_Usuarios WHERE nome_completo = ?", (usuario_nome_completo,))
        resultado = c.fetchone()
        if not resultado:
            return False
        
        caminho_relativo_db = resultado[0]
        caminho_absoluto_foto = os.path.join(BASE_DIR, caminho_relativo_db)

        c.execute("DELETE FROM app_Usuarios WHERE nome_completo = ?", (usuario_nome_completo,))
        conn.commit()
        
        if os.path.exists(caminho_absoluto_foto):
            os.remove(caminho_absoluto_foto)
        
        return True
    finally:
        conn.close()


def excluir_usuario(usuario_nome_completo):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("SELECT caminho_foto_rosto FROM app_Usuarios WHERE nome_completo = ?", (usuario_nome_completo,))
        resultado = c.fetchone()
        if not resultado:
            return False
        
        caminho_relativo_db = resultado[0]
        # CORREÇÃO: Monta o caminho absoluto para encontrar o ficheiro a apagar
        caminho_absoluto_foto = os.path.join(BASE_DIR, caminho_relativo_db)

        c.execute("DELETE FROM app_Usuarios WHERE nome_completo = ?", (usuario_nome_completo,))
        conn.commit()
        
        if os.path.exists(caminho_absoluto_foto):
            os.remove(caminho_absoluto_foto)
        
        return True
    finally:
        conn.close()


def excluir_usuario(usuario_nome_completo):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("SELECT caminho_foto_rosto FROM app_Usuarios WHERE nome_completo = ?", (usuario_nome_completo,))
        resultado = c.fetchone()
        if not resultado:
            return False
        
        caminho_relativo_db = resultado[0]
        # CORREÇÃO: Monta o caminho absoluto para encontrar o ficheiro a apagar
        caminho_absoluto_foto = os.path.join(BASE_DIR, caminho_relativo_db)

        c.execute("DELETE FROM app_Usuarios WHERE nome_completo = ?", (usuario_nome_completo,))
        conn.commit()
        
        if os.path.exists(caminho_absoluto_foto):
            os.remove(caminho_absoluto_foto)
        
        return True
    finally:
        conn.close()


def listar_todos_usuarios():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM app_Usuarios ORDER BY nome_completo")
        usuarios = [dict(row) for row in c.fetchall()]
        return usuarios
    except Exception as e:
        print(f"falha ao listar usuários: {e}")
        return []
    finally:
        conn.close()

def buscar_usuario(termo_busca):

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        termo = f"%{termo_busca}%"
        c.execute("SELECT * FROM app_Usuarios WHERE nome_completo LIKE ? OR matricula LIKE ?", (termo, termo))
        usuarios = [dict(row) for row in c.fetchall()]
        return usuarios
    except Exception as e:
        print(f"falha ao buscar usuário: {e}")
        return []
    finally:
        conn.close()





#cadastrar_usuario("TESTE", 0000000, "Discente", ".\Rostos_cadastrados\este.jpg")

#cadastrar_curso("Informática")
#cadastrar_usuario("juan", 1111111, "Discente", ".\capturas_log\juan.jpg")
#print(listar_todos_usuarios())
#excluir_usuario('TESTE')

# Exemplo de como chamar a nova função



def cadastrar_visitante(nome, documento, empresa, motivo, horario_inicio, horario_fim):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sql = '''
        INSERT INTO app_Visitantes (nome_completo, documento, empresa, motivo_acesso, horario_programado_inicio, horario_programado_fim)
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    try:
        c.execute(sql, (nome, documento, empresa, motivo, horario_inicio, horario_fim))
        conn.commit()
        novo_id = c.lastrowid
        print(f"Visitante '{nome}' cadastrado com sucesso com ID {novo_id}.")
        return novo_id
    except Exception as e:
        print(f"Falha ao cadastrar visitante: {e}")
        return None
    finally:
        conn.close()

def listar_visitantes_agendados(data):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sql = "SELECT * FROM app_Visitantes WHERE date(horario_programado_inicio) = ? ORDER BY horario_programado_inicio"
    try:
        c.execute(sql, (data,))
        visitantes = [dict(row) for row in c.fetchall()]
        return visitantes
    except Exception as e:
        print(f"[ERRO] Falha ao listar visitantes: {e}")
        return []
    finally:
        conn.close()

def listar_logs_recentes(limite=5):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sql = """
        SELECT
            L.timestamp_acesso,
            L.status,
            U.nome_completo
        FROM app_LogsAcesso L
        LEFT JOIN app_Usuarios U ON L.usuario_id = U.id
        ORDER BY L.timestamp_acesso DESC
        LIMIT ?
    """
    try:
        c.execute(sql, (limite,))
        logs = [dict(row) for row in c.fetchall()]
        return logs
    except Exception as e:
        print(f"Falha ao listar logs recentes: {e}")
        return []
    finally:
        conn.close()



def criar_curso(nome_curso):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sql = "INSERT INTO app_Cursos (nome_curso) VALUES (?)"
    try:
        c.execute(sql, (nome_curso,))
        conn.commit()
        novo_id = c.lastrowid
        print(f"Curso '{nome_curso}' criado com sucesso com ID {novo_id}.")
        return novo_id
    except sqlite3.IntegrityError:
        print(f"O curso '{nome_curso}' já existe.")
        return None
    except Exception as e:
        print(f"Falha ao criar curso: {e}")
        return None
    finally:
        conn.close()

def listar_cursos():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sql = "SELECT * FROM app_Cursos ORDER BY nome_curso"
    try:
        c.execute(sql)
        cursos = [dict(row) for row in c.fetchall()]
        return cursos
    except Exception as e:
        print(f"Falha ao listar cursos: {e}")
        return []
    finally:
        conn.close()

def criar_turma(nome_turma, curso_id, ano, turno):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sql = "INSERT INTO app_Turmas (nome_turma, curso_id, ano, turno) VALUES (?, ?, ?, ?)"
    try:
        c.execute(sql, (nome_turma, curso_id, ano, turno))
        conn.commit()
        novo_id = c.lastrowid
        print(f"Turma '{nome_turma}' criada com sucesso com ID {novo_id}.")
        return novo_id
    except Exception as e:
        print(f"Falha ao criar turma: {e}")
        return None
    finally:
        conn.close()

def listar_turmas(curso_id=None):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    sql = """
        SELECT T.id, T.nome_turma, T.ano, T.turno, C.nome_curso
        FROM app_Turmas T
        JOIN app_Cursos C ON T.curso_id = C.id
    """
    params = []
    if curso_id:
        sql += " WHERE T.curso_id = ?"
        params.append(curso_id)
        
    sql += " ORDER BY C.nome_curso, T.nome_turma"
    
    try:
        c.execute(sql, params)
        turmas = [dict(row) for row in c.fetchall()]
        return turmas
    except Exception as e:
        print(f"Falha ao listar turmas: {e}")
        return []
    finally:
        conn.close()

def editar_turma(turma_id, novos_dados):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    set_clause = ", ".join([f"{key} = ?" for key in novos_dados.keys()])
    values = list(novos_dados.values())
    values.append(turma_id)
    sql = f"UPDATE app_Turmas SET {set_clause} WHERE id = ?"
    try:
        c.execute(sql, tuple(values))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        print(f"Falha ao editar turma: {e}")
        return False
    finally:
        conn.close()

def excluir_turma(turma_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM app_UsuarioTurma WHERE turma_id = ?", (turma_id,))
        c.execute("DELETE FROM app_Turmas WHERE id = ?", (turma_id,))
        conn.commit()
        print(f"Turma ID {turma_id} e seus vínculos foram excluídos.")
        return True
    except Exception as e:
        print(f"Falha ao excluir turma: {e}")
        return False
    finally:
        conn.close()



def aplicar_sancao(usuario_id, operador_id, tipo, motivo, data_inicio, data_fim):
    """
    Aplica uma sanção (Advertência ou Suspensão) a um utilizador.
    Esta função atualiza a situação do utilizador e regista a ação na base de dados.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:

        nova_situacao = 'Suspenso' if tipo == 'Suspensão' else 'Advertido'
        sql_update_usuario = "UPDATE app_Usuarios SET situacao = ? WHERE id = ?"
        c.execute(sql_update_usuario, (nova_situacao, usuario_id))


        sql_insert_sancao = """
            INSERT INTO app_AcoesDisciplinares (usuario_id, operador_id, tipo, motivo, data_inicio, data_fim)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        c.execute(sql_insert_sancao, (usuario_id, operador_id, tipo, motivo, data_inicio, data_fim))
        
        conn.commit()
        print(f"[INFO] Sanção '{tipo}' aplicada com sucesso ao utilizador ID {usuario_id}.")
        return True
    except Exception as e:
        conn.rollback() 
        print(f"[ERRO] Falha ao aplicar sanção: {e}")
        return False
    finally:
        conn.close()


def cadastrar_liberacao_coapac(turma_id, operador_id, justificativa, data_liberacao, horario_liberacao):

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    sql = '''
        INSERT INTO app_LiberacoesCOAPAC (turma_id, operador_id, justificativa, data_liberacao, horario_liberacao)
        VALUES (?, ?, ?, ?, ?)
    '''
    try:
        c.execute(sql, (turma_id, operador_id, justificativa, data_liberacao, horario_liberacao))
        conn.commit()
        novo_id = c.lastrowid
        print(f"Liberação da COAPAC registrada com sucesso com ID {novo_id}.")
        return novo_id
    except Exception as e:
        print(f"[ERRO] Falha ao cadastrar liberação da COAPAC: {e}")
        return None
    finally:
        conn.close()

def excluir_liberacao_coapac(liberacao_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    sql = "DELETE FROM app_LiberacoesCOAPAC WHERE id = ?"
    try:
        c.execute(sql, (liberacao_id,))
        conn.commit()
        if c.rowcount > 0:
            print(f"Liberação ID {liberacao_id} excluída com sucesso.")
            return True
        else:
            print(f"Nenhuma liberação encontrada com o ID {liberacao_id}.")
            return False
    except Exception as e:
        print(f"[ERRO] Falha ao excluir liberação: {e}")
        return False
    finally:
        conn.close()

def listar_liberacoes_coapac_atuais():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    agora = datetime.now()
    data_hoje = agora.strftime("%Y-%m-%d")
    hora_agora = agora.strftime("%H:%M:%S")

    sql = '''
        SELECT 
            L.id, L.justificativa, L.data_liberacao, L.horario_liberacao,
            T.nome_turma,
            O.nome as nome_operador
        FROM app_LiberacoesCOAPAC L
        JOIN app_Turmas T ON L.turma_id = T.id
        JOIN app_Operadores O ON L.operador_id = O.id
        WHERE
            (L.data_liberacao > ?)
            OR (L.data_liberacao = ? AND L.horario_liberacao >= ?)
        ORDER BY L.data_liberacao, L.horario_liberacao
    '''
    try:
        c.execute(sql, (data_hoje, data_hoje, hora_agora))
        permissoes = [dict(row) for row in c.fetchall()]
        return permissoes
    except Exception as e:
        print(f"Falha ao listar liberações atuais da COAPAC: {e}")
        return []
    finally:
        conn.close()

def conceder_permissao_especial(usuario_id, operador_id, justificativa, data_hora_permissao):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sql = """
        INSERT INTO app_PermissoesEspeciais (usuario_id, operador_id, justificativa, data_hora_permissao)
        VALUES (?, ?, ?, ?)
    """
    try:
        c.execute(sql, (usuario_id, operador_id, justificativa, data_hora_permissao))
        conn.commit()
        print(f"Permissão especial concedida para o utilizador ID {usuario_id} com sucesso.")
        return True
    except Exception as e:
        print(f"Falha ao conceder permissão especial: {e}")
        return False
    finally:
        conn.close()

def listar_permissoes_especiais():

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sql = """
        SELECT
            P.id,
            P.justificativa,
            P.data_hora_permissao,
            U.nome_completo as nome_usuario,
            O.nome as nome_operador
        FROM app_PermissoesEspeciais P
        JOIN app_Usuarios U ON P.usuario_id = U.id
        JOIN app_Operadores O ON P.operador_id = O.id
        ORDER BY P.data_hora_permissao DESC
    """
    try:
        c.execute(sql)
        permissoes = [dict(row) for row in c.fetchall()]
        return permissoes
    except Exception as e:
        print(f"[ERRO] Falha ao listar permissões especiais: {e}")
        return []
    finally:
        conn.close()


def contar_acessos_hoje():
    """
    Conta quantos acessos (aceites, negados, etc.) foram registados no dia de hoje.
    Retorna:
        Um número inteiro com a contagem total de acessos.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    sql = "SELECT COUNT(*) FROM app_LogsAcesso WHERE date(timestamp_acesso) = ?"
    try:
        c.execute(sql, (data_hoje,))
        # c.fetchone() retorna uma tupla, ex: (25,). A contagem está no primeiro elemento.
        contagem = c.fetchone()[0]
        return contagem
    except Exception as e:
        print(f"[ERRO] Falha ao contar acessos de hoje: {e}")
        return 0
    finally:
        conn.close()

def contar_visitantes_hoje():
    """
    Conta quantos visitantes estão agendados para o dia de hoje.
    Retorna:
        Um número inteiro com a contagem de visitantes.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    sql = "SELECT COUNT(*) FROM app_Visitantes WHERE date(horario_programado_inicio) = ?"
    try:
        c.execute(sql, (data_hoje,))
        contagem = c.fetchone()[0]
        return contagem
    except Exception as e:
        print(f"[ERRO] Falha ao contar visitantes de hoje: {e}")
        return 0
    finally:
        conn.close()

def contar_sancoes_ativas():
    """
    Conta quantos utilizadores estão atualmente com a situação 'Suspenso' ou 'Advertido'.
    Retorna:
        Um número inteiro com a contagem de sanções ativas.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sql = "SELECT COUNT(*) FROM app_Usuarios WHERE situacao IN ('Suspenso', 'Advertido')"
    try:
        c.execute(sql)
        contagem = c.fetchone()[0]
        return contagem
    except Exception as e:
        print(f"[ERRO] Falha ao contar sanções ativas: {e}")
        return 0
    finally:
        conn.close()


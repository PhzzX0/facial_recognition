import sqlite3
import os
import cv2
from datetime import datetime
from deepface import DeepFace


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'database.db')
capturas_dir = os.path.join(BASE_DIR, 'capturas_log')
rostos_dir = os.path.join(BASE_DIR, 'rostos_cadastrados') 

os.makedirs(capturas_dir, exist_ok=True)
os.makedirs(rostos_dir, exist_ok=True)




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
        print(f"evento de acesso '{status}' registrado às {timestamp_local}.")
    except Exception as e:
        print(f"Não foi possível registrar o acesso: {e}")
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
            print("[AVISO] Nenhum usuário cadastrado para verificação.")
            registrar_log_acesso('Não Encontrado', caminho_foto_capturada=log_img_path)
            return
        
        pessoa_encontrada = False
        for user_id, nome, arquivo_rosto_db in registros:
            if not os.path.exists(arquivo_rosto_db):
                continue
            
            try:
                result = DeepFace.verify(img1_path=log_img_path, img2_path=arquivo_rosto_db, model_name='Facenet512', enforce_detection=False)
                
                if result['verified']:
                    pessoa_encontrada = True
                    c.execute("""
                        SELECT U.nome_completo, U.matricula, U.tipo, U.situacao, T.nome_turma, C.nome_curso
                        FROM app_Usuarios U
                        LEFT JOIN app_UsuarioTurma UT ON U.id = UT.usuario_id
                        LEFT JOIN app_Turmas T ON UT.turma_id = T.id
                        LEFT JOIN app_Cursos C ON T.curso_id = C.id
                        WHERE U.id = ?
                    """, (user_id,))
                    detalhes = c.fetchone()
                    
                    nome_completo, matricula, tipo, situacao, turma, curso = detalhes

                    print("-" * 30)
                    if situacao == 'Suspenso':
                        print(f"ACESSO NEGADO: {nome_completo}")
                        print(f"   - Motivo: Usuário com situação '{situacao}'")
                        registrar_log_acesso('Negado', user_id, log_img_path)
                    else:
                        print(f"ACESSO ACEITO: {nome_completo}")
                        print(f"   - Matrícula: {matricula or 'N/A'}")
                        print(f"   - Tipo: {tipo}")
                        print(f"   - Situação: {situacao}")
                        if tipo == 'Discente':
                            print(f"   - Curso: {curso or 'Não vinculado'}")
                            print(f"   - Turma: {turma or 'Não vinculada'}")
                        registrar_log_acesso('Aceito', user_id, log_img_path)
                    print("-" * 30)
                    return

            except Exception as e:
                print(f"Verificação falhou para {nome}. Detalhe: {e}")

        if not pessoa_encontrada:
            print("Pessoa não reconhecida no banco de dados.")
            registrar_log_acesso('Não Encontrado', caminho_foto_capturada=log_img_path)
    finally:
        conn.close()

def cadastrar_usuario(nome, matricula, tipo, caminho_foto):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Salva o arquivo de imagem do rosto
    #caminho_foto = os.path.join(rostos_dir, f"{matricula}.jpg")
    #cv2.imwrite(caminho_foto, imagem_rosto)
    
    try:
        c.execute('''
            INSERT INTO app_Usuarios (nome_completo, matricula, tipo, caminho_foto_rosto)
            VALUES (?, ?, ?, ?)
        ''', (nome, matricula, tipo, caminho_foto))
        conn.commit()
        novo_id = c.lastrowid
        print(f"[usuário '{nome}' cadastrado com sucesso com ID {novo_id}.")
        return novo_id
    except sqlite3.IntegrityError:
        print(f"[matrícula '{matricula}' já existe. Cadastro cancelado.")
        os.remove(caminho_foto) # Remove a foto se o cadastro falhar
        return None
    except Exception as e:
        print(f"falha ao cadastrar usuário: {e}")
        return None
    finally:
        conn.close()



def editar_usuario(usuario_id, novos_dados):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    set_clause = ", ".join([f"{key} = ?" for key in novos_dados.keys()])
    values = list(novos_dados.values())
    values.append(usuario_id)
    
    query = f"UPDATE app_Usuarios SET {set_clause} WHERE id = ?"
    
    try:
        c.execute(query, tuple(values))
        conn.commit()
        if c.rowcount == 0:
            print(f"nenhum usuário encontrado com ID {usuario_id}.")
            return False
        print(f"usuário ID {usuario_id} atualizado com sucesso.")
        return True
    except Exception as e:
        print(f"falha ao editar usuário: {e}")
        return False
    finally:
        conn.close()

def excluir_usuario(usuario_nome_completo):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("SELECT caminho_foto_rosto FROM app_Usuarios WHERE nome_completo = ?", (usuario_nome_completo,))
        resultado = c.fetchone()
        if not resultado:
            print(f"[AVISO] Nenhum usuário encontrado com nome {usuario_nome_completo}.")
            return False
        
        caminho_foto = resultado[0]
        c.execute("DELETE FROM app_Usuarios WHERE nome_completo = ?", (usuario_nome_completo,))
        conn.commit()
        
        # Exclui o arquivo da foto
        if os.path.exists(caminho_foto):
            os.remove(caminho_foto)
            
        print(f"usuário {usuario_nome_completo} e sua foto foram excluídos com sucesso.")
        return True
    except Exception as e:
        print(f"falha ao excluir usuário: {e}")
        return False
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





#cadastrar_usuario("JOABE TORRES FERREIRA", 20221084010001, "Discente", ".\Rostos_cadastrados\joabe.jpg")

#cadastrar_curso("Informática")
#cadastrar_usuario("juan", 1111111, "Discente", ".\capturas_log\juan.jpg")
#print(listar_todos_usuarios())

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

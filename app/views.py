from django.shortcuts import render, redirect
from .models import (Operadores, LogAcesso, Usuario, Curso, Turma, UsuarioTurma, Visitante)
from .forms import FormPermissaoEspecial
import hashlib
import os
import sqlite3
from django.http import StreamingHttpResponse, JsonResponse
import cv2
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import base64
import uuid
import numpy as np
import json
from core_functions import verificar_pessoa
import mediapipe as mp
import json

mp_face_detection = mp.solutions.face_detection

@csrf_exempt
def receber_imagem(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        imagem_base64 = data.get('imagem', '')
        
        if not imagem_base64.startswith('data:image'):
            return JsonResponse({'erro': 'Imagem inválida'}, status=400)

        # Extrai apenas os dados base64
        _, base64_data = imagem_base64.split(',', 1)
        imagem_bytes = base64.b64decode(base64_data)

        # Converte os bytes para array numpy e depois para imagem OpenCV
        np_arr = np.frombuffer(imagem_bytes, np.uint8)
        imagem = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # BGR

        # Inicializa o detector de rosto do MediaPipe
        with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6) as face_detection:
            rgb_frame = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb_frame)

            if not results.detections:
                return JsonResponse({'erro': 'Nenhum rosto detectado'}, status=400)

            # Usa o primeiro rosto detectado
            detection = results.detections[0]
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = imagem.shape
            x = int(bboxC.xmin * iw)
            y = int(bboxC.ymin * ih)
            w = int(bboxC.width * iw)
            h = int(bboxC.height * ih)
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(iw, x + w), min(ih, y + h)

            # Recorta o rosto da imagem
            rosto = imagem[y1:y2, x1:x2]

            if rosto.size == 0:
                return JsonResponse({'erro': 'Falha ao recortar rosto'}, status=500)

            # Chama a função de verificação facial
            resposta = verificar_pessoa(rosto)

            print(resposta)
            if resposta["resposta"] == 1:
                if resposta["dados"]: request.session['dados'] = resposta["dados"]
                return JsonResponse({"redirect": "/acesso_negado/"})
            elif resposta["resposta"] == 2:
                request.session['dados'] = resposta["dados"]
                return JsonResponse({"redirect": "/acesso_permitido/"})

    return JsonResponse({'erro': 'Método inválido'}, status=405)

def aluno(request):
    return render(request, "Tela_Aluno_portaria.html")

def negado(request):
    dados = request.session.get('dados', {})
    return render(request, "Acesso_Negado.html", dados)

def permitido(request):
    dados = request.session.get('dados', {})
    return render(request, 'Acesso_permitido.html', dados)

def index(request):
	if 'operador_id' not in request.session: # verifica se ha um usuario logado
		return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login

	return redirect("dashboard") # redireciona para a pagina dashboard se o usuario estiver logado


def login(request):
	if request.method == "POST":
		usuario = request.POST["usuario"] # pega o campo usuario do html
		senha = request.POST["senha"] # pega o campo senha do html
		senha_hash = hashlib.sha256(senha.encode()).hexdigest() # criptografa a senha em sha256
		try: # tenta encontrar um usuario com o nome fornecido
			operador = Operadores.objects.get(login=usuario) # cria uma variavel para esse usuario 
			if operador.senha_hash == senha_hash: # compara a senha para verificar se esta correta
				request.session['operador_id'] = operador.id	
				return redirect("dashboard") # se a senha estiver correta redireciona para a pagina dashboard
			else:
				erro = 'Senha incorreta' # mensagem de erro
		except Operadores.DoesNotExist: # se o usuario nao for encontrado no banco de dados
			erro = 'Usuario nao encontrado' # mensagem de erro
		return render(request, "login.html", {"erro": erro}) # carrega a pagina de login com a mensagem de erro
	return render(request, "login.html") # carrega a pagina de login


def logout(request):
	request.session.flush() # encerra a sessao do usuario(desloga)
	return redirect("login") # redireciona para a pagina


def dashboard(request):
    if 'operador_id' not in request.session: # verifica se ha um usuario logado
        return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login
    operador = Operadores.objects.get(id=request.session['operador_id']) # variavel para o usuario logado
    
    if operador.papel == "COAPAC":
        return render(request, "inicio.html", {"papel": operador.papel})
    elif operador.papel == "Porteiro":
        return render(request, "porteiro.html", {"papel": operador.papel})


def usuarios(request):
	if 'operador_id' not in request.session: # verifica se ha um usuario logado
		return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login
	operador = Operadores.objects.get(id=request.session['operador_id']) # variavel para o usuario logado
	
	return render(request, "usuarios.html") # carrega a pagina usuarios


# Função para obter conexão com o banco de dados SQLite
def get_db_connection():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/
    db_path = os.path.join(BASE_DIR, '..', 'database.db')  # facial_recognition/database.db
    db_path = os.path.abspath(db_path)  # Garante caminho completo
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def turmas(request):
    if 'operador_id' not in request.session: # verifica se ha um usuario logado
        return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login

    conn = get_db_connection()

    # Consulta todas as turmas com seus respectivos cursos
    turmas = conn.execute("""
        SELECT t.id, t.nome_turma, t.turno, t.ano, t.curso_id,
               c.nome_curso
        FROM app_Turmas t
        JOIN app_Cursos c ON t.curso_id = c.id
        ORDER BY c.nome_curso, t.ano DESC
    """).fetchall()

    cursos_organizados = {}
    for turma in turmas:
        curso_nome = turma["nome_curso"]
        if curso_nome not in cursos_organizados:
            cursos_organizados[curso_nome] = []
        cursos_organizados[curso_nome].append(turma)

    # Lógica do painel registros
    ver_todos = False
    if request.method == "POST":
        ver_todos = request.POST.get("ver_todos") == "1"

    c = conn.cursor()
    # Consulta os registros de liberações com base no dia atual ou todos
    if ver_todos:
        c.execute("""
            SELECT data_liberacao, horario_liberacao, justificativa 
            FROM app_LiberacoesCOAPAC 
            ORDER BY data_liberacao DESC, horario_liberacao DESC
        """)
    else:
        hoje = datetime.now().date().isoformat()
        c.execute("""
            SELECT data_liberacao, horario_liberacao, justificativa 
            FROM app_LiberacoesCOAPAC 
            WHERE data_liberacao = ? 
            ORDER BY horario_liberacao DESC
        """, (hoje,))
    # Transforma os dados em dicionários para o template
    registros = [{
        "data": r[0],
        "horario": r[1],
        "status": r[2]  # Aqui usamos 'justificativa' como status no painel
    } for r in c.fetchall()]


    conn.close()
    # Renderiza o template com os dados organizados
    return render(request, 'turmas.html', {
        'cursos': cursos_organizados,
        'registros': registros,
        'ver_todos': ver_todos,
    })

# View para adicionar nova turma
def adicionar_turma(request):
    if request.method == 'POST':
        nome_turma = request.POST.get('nome_turma')
        curso_id = request.POST.get('curso_id')
        ano = request.POST.get('ano')
        turno = request.POST.get('turno')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verifica se já existe turma com mesmo curso, ano e turno
        cursor.execute(
            "SELECT COUNT(*) FROM app_Turmas WHERE curso_id = ? AND ano = ? AND turno = ?",
            (curso_id, ano, turno)
        )
        (count,) = cursor.fetchone()

        if count > 0:
            # Busca os cursos para exibir no template
            cursor.execute("SELECT id, nome_curso FROM app_Cursos")
            cursos = cursor.fetchall()
            conn.close()
            return render(request, 'adicionar_turma.html', {
                'cursos': cursos,
                'error': 'Já existe uma turma para esse curso, ano e turno.'
            })

        # Se não existir, insere normalmente
        cursor.execute(
            "INSERT INTO app_Turmas (nome_turma, curso_id, ano, turno) VALUES (?, ?, ?, ?)",
            (nome_turma, curso_id, ano, turno)
        )
        conn.commit()
        conn.close()

        return redirect('turmas')
	
    # Se não for POST, apenas exibe o formulário com os cursos
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_curso FROM app_Cursos")
    cursos = cursor.fetchall()
    conn.close()

    return render(request, 'adicionar_turma.html', {'cursos': cursos})

# View que lida com exclusão de turmas via POST
def deletar_turma(request, turma_id):
    print("Método:", request.method)
    print("Turma ID recebido:", turma_id)
    if request.method == 'POST':
        try:
            turma_id = int(turma_id)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM app_Turmas WHERE id = ?", (turma_id,))
            print("Linhas deletadas:", cursor.rowcount)
            conn.commit()
            conn.close()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            print("Erro:", e)
            return JsonResponse({'status': 'erro', 'mensagem': str(e)}, status=500)
    return JsonResponse({'status': 'erro', 'mensagem': 'Método não permitido'}, status=405)



def registro(request):
	if 'operador_id' not in request.session: # verifica se ha um usuario logado
		return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login
	operador = Operadores.objects.get(id=request.session['operador_id']) # variavel para o usuario logado

	return render(request, "registro.html") # carrega a pagina registro

# ------------------ PERMISSÕES ESPECIAIS ------------------

from datetime import datetime

def permissoes(request):
    if 'operador_id' not in request.session: # verifica se ha um usuario logado
        return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login
    operador = Operadores.objects.get(id=request.session['operador_id']) # variavel para o usuario logado   
    logs = LogAcesso.objects.order_by('-timestamp_acesso')[:5] # Pega os últimos 5 logs de acesso
    for log in logs:
        try:
            log.timestamp_dt = datetime.strptime(log.timestamp_acesso, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            log.timestamp_dt = None
    # aqui abaixo é o código para criar uma nova permissão especial, ainda não está pronto
    if request.method == "POST":
        matricula = request.POST.get("usuario")
        try:
            usuario = Usuarios.objects.get(matricula=matricula)
            nova_permissao = PermissaoEspecial.objects.create(
                usuario=usuario,
                operador=operador,
                data_hora_permissao=timezone.now()
            )
        except Usuarios.DoesNotExist:
            pass

        return redirect("permissoes") 

    return render(request, "permissoes.html", {
        "logs": logs,
        "operador": operador,
    })#renderiza a pagina permissoes com as variaveis logs e operador
    if 'operador_id' not in request.session:
        return redirect("login")

    operador = Operadores.objects.get(id=request.session['operador_id'])

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifica se precisa mostrar todos ou só do dia
    ver_todos = request.GET.get('ver_todos') == '1'

    if ver_todos:
        cursor.execute("""
            SELECT l.timestamp_acesso, l.status, u.nome_completo AS usuario_nome, v.nome_completo AS visitante_nome
            FROM app_LogsAcesso l
            LEFT JOIN app_Usuarios u ON l.usuario_id = u.id
            LEFT JOIN app_Visitantes v ON l.visitante_id = v.id
            ORDER BY l.timestamp_acesso DESC
            LIMIT 50
        """)
    else:
        hoje = datetime.now().date().isoformat()
        cursor.execute("""
            SELECT l.timestamp_acesso, l.status, u.nome_completo AS usuario_nome, v.nome_completo AS visitante_nome
            FROM app_LogsAcesso l
            LEFT JOIN app_Usuarios u ON l.usuario_id = u.id
            LEFT JOIN app_Visitantes v ON l.visitante_id = v.id
            WHERE DATE(l.timestamp_acesso) = ?
            ORDER BY l.timestamp_acesso DESC
            LIMIT 50
        """, (hoje,))

    logs = cursor.fetchall()
    conn.close()

    # Converte para lista de dicionários com hora e data formatadas
    lista_logs = []
    for log in logs:
        try:
            dt = datetime.strptime(log["timestamp_acesso"], "%Y-%m-%d %H:%M:%S")
            data_formatada = dt.strftime("%b %d, %Y")  # exemplo: Aug 06, 2025
            hora = dt.strftime("%H:%M")
        except Exception:
            data_formatada = log["timestamp_acesso"]
            hora = ""

        lista_logs.append({
            "data_formatada": data_formatada,
            "hora": hora,
            "status": log["status"],
            "usuario_nome": log["usuario_nome"],
            "visitante_nome": log["visitante_nome"]
        })

    return render(request, "permissoes.html", {
        "operador_nome": operador.nome,
        "logs": lista_logs,
        "ver_todos": ver_todos
    })


# Buscar usuário para autocomplete por nome ou matrícula (GET com param "q")
def buscar_usuario(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, nome_completo, matricula FROM app_Usuarios
        WHERE nome_completo LIKE ? OR matricula LIKE ?
        LIMIT 10
    """, (f'%{query}%', f'%{query}%'))
    resultados = [{"id": row["id"], "nome": row["nome_completo"], "matricula": row["matricula"]} for row in c.fetchall()]
    conn.close()
    return JsonResponse(resultados, safe=False)

# Recebe POST para conceder permissão especial
@csrf_exempt
def conceder_permissao_especial(request):
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)
    if 'operador_id' not in request.session:
        return JsonResponse({'erro': 'Usuário não autenticado'}, status=401)

    data = json.loads(request.body)
    usuario_id = data.get('usuario_id')
    justificativa = data.get('justificativa')
    data_permissao = data.get('data')
    hora_permissao = data.get('hora')
    operador_id = request.session['operador_id']

    if not all([usuario_id, justificativa, data_permissao, hora_permissao]):
        return JsonResponse({'erro': 'Campos obrigatórios faltando'}, status=400)

    data_hora = f"{data_permissao} {hora_permissao}:00"

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO app_PermissoesEspeciais (usuario_id, operador_id, justificativa, data_hora_permissao)
        VALUES (?, ?, ?, ?)
    """, (usuario_id, operador_id, justificativa, data_hora))
    conn.commit()
    conn.close()

    return JsonResponse({'status': 'ok'})

# Lista todas permissões especiais (GET)
def listar_permissoes_especiais(request):
    if 'operador_id' not in request.session:
        return JsonResponse({'erro': 'Usuário não autenticado'}, status=401)

    conn = get_db_connection()
    permissoes = conn.execute("""
        SELECT pe.id, u.nome_completo AS usuario_nome, u.matricula, pe.justificativa,
               o.nome AS operador_nome, pe.data_hora_permissao
        FROM app_PermissoesEspeciais pe
        JOIN app_Usuarios u ON pe.usuario_id = u.id
        JOIN app_Operadores o ON pe.operador_id = o.id
        ORDER BY pe.data_hora_permissao DESC
    """).fetchall()
    conn.close()

    lista = [{
        "id": p["id"],
        "usuario_nome": p["usuario_nome"],
        "matricula": p["matricula"],
        "justificativa": p["justificativa"],
        "operador_nome": p["operador_nome"],
        "data_hora_permissao": p["data_hora_permissao"]
    } for p in permissoes]

    return JsonResponse(lista, safe=False)

def suspensoes(request):
	if 'operador_id' not in request.session: # verifica se ha um usuario logado
		return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login
	operador = Operadores.objects.get(id=request.session['operador_id']) # variavel para o usuario logado

	return render(request, "suspensoes.html") # carrega a pagina suspensoes


def acessoExterno(request):
	if 'operador_id' not in request.session: # verifica se ha um usuario logado
		return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login
	operador = Operadores.objects.get(id=request.session['operador_id']) # variavel para o usuario logado

	return render(request, "acessoExterno.html") # carrega a pagina acesso externo





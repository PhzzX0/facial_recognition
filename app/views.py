from django.shortcuts import render, redirect
from .models import Operadores
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
#def verificar_pessoa(imagem):
    # Simula processamento leve
    #return {"resposta": 2, "dados": {"nome": "João", "matricula": "2222222222"}}

# Captura da câmera
#camera = cv2.VideoCapture(0)

#def generate_frames():
#    while True:
#        success, frame = camera.read()
#        if not success:
#            break
#        else:
#            ret, buffer = cv2.imencode('.jpg', frame)
#            frame = buffer.tobytes()
#            yield (b'--frame\r\n'
#                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


#def video_feed(request):
#    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

@csrf_exempt
def receber_imagem(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        imagem_base64 = data.get('imagem', '')
        
        if not imagem_base64.startswith('data:image'):
            return JsonResponse({'erro': 'Imagem inválida'}, status=400)

        # Extrai apenas os dados base64 (removendo o cabeçalho data:image/jpeg;base64,...)
        _, base64_data = imagem_base64.split(',', 1)
        imagem_bytes = base64.b64decode(base64_data)

        # Converte os bytes para array numpy e depois para imagem OpenCV
        np_arr = np.frombuffer(imagem_bytes, np.uint8)
        imagem = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # BGR

        # -------- PROCESSAMENTO COM OPENCV AQUI -------- #
        resposta = verificar_pessoa(imagem)
        # ------------------------------------------------ #
        print(resposta)
        if resposta["resposta"] == 1:
            return JsonResponse({"redirect": "/acesso_negado/"})
        elif resposta["resposta"] == 2:
            request.session['dados'] = resposta["dados"]
            return JsonResponse({"redirect": "/acesso_permitido/"})
        

    return JsonResponse({'erro': 'Método inválido'}, status=405)

def aluno(request):
    return render(request, "Tela_Aluno_portaria.html")

def negado(request):
    return render(request, "Acesso_Negado.html")

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
        return render(request, "inicial.html", {"papel": operador.papel})
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


def permissoes(request):
	if 'operador_id' not in request.session: # verifica se ha um usuario logado
		return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login
	operador = Operadores.objects.get(id=request.session['operador_id']) # variavel para o usuario logado

	return render(request, "permissoes.html") # carrega a pagina permissoes


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



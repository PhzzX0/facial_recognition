from django.shortcuts import render, redirect, get_object_or_404
from .models import (Operadores, LogAcesso, Usuario, Curso, Turma, UsuarioTurma, Visitante, PermissaoEspecial)
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
# app/views.py
from core_functions import verificar_pessoa, buscar_logs_filtrados, cadastrar_usuario_core, criar_turma, db_path
import mediapipe as mp
from django.utils.timezone import now
from django.conf import settings
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef


mp_face_detection = mp.solutions.face_detection

@csrf_exempt
def receber_imagem(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        imagem_base64 = data.get('imagem', '')
        
        if not imagem_base64.startswith('data:image'):
            return JsonResponse({'erro': 'Imagem inválida'}, status=400)

        _, base64_data = imagem_base64.split(',', 1)
        imagem_bytes = base64.b64decode(base64_data)
        np_arr = np.frombuffer(imagem_bytes, np.uint8)
        imagem = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6) as face_detection:
            rgb_frame = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb_frame)

            if not results.detections:
                return JsonResponse({'erro': 'Nenhum rosto detectado'}, status=400)

            detection = results.detections[0]
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = imagem.shape
            x = int(bboxC.xmin * iw)
            y = int(bboxC.ymin * ih)
            w = int(bboxC.width * iw)
            h = int(bboxC.height * ih)
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(iw, x + w), min(ih, y + h)
            rosto = imagem[y1:y2, x1:x2]

            if rosto.size == 0:
                return JsonResponse({'erro': 'Falha ao recortar rosto'}, status=500)

            resposta = verificar_pessoa(rosto)
            if resposta["resposta"] == 1:
                request.session['dados'] = resposta["dados"]
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
    if 'operador_id' not in request.session:
        return redirect("login")
    return redirect("dashboard")

def login(request):
    if request.method == "POST":
        usuario = request.POST["usuario"]
        senha = request.POST["senha"]
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        try:
            operador = Operadores.objects.get(login=usuario)
            if operador.senha_hash == senha_hash:
                request.session['operador_id'] = operador.id
                return redirect("dashboard")
            else:
                erro = 'Senha incorreta'
        except Operadores.DoesNotExist:
            erro = 'Usuário não encontrado'
        return render(request, "login.html", {"erro": erro})
    return render(request, "login.html")

def logout(request):
    request.session.flush()
    return redirect("login")

def dashboard(request):
    if 'operador_id' not in request.session:
        return redirect("login")
    operador = Operadores.objects.get(id=request.session['operador_id'])
    total_usuarios = Usuario.objects.count()
    total_turmas = Turma.objects.count()
    total_registros = LogAcesso.objects.count()
    usuarios_ativos = Usuario.objects.filter(situacao="Normal").count()
    acessos_hoje = LogAcesso.objects.filter(timestamp_acesso__startswith=now().strftime("%Y-%m-%d")).count()
    return render(request, "inicio.html", {
        "papel": operador.papel,
        "total_usuarios": total_usuarios,
        "total_turmas": total_turmas,
        "total_registros": total_registros,
        "usuarios_ativos": usuarios_ativos,
        "acessos_hoje": acessos_hoje,
    })

def usuarios(request):
    if 'operador_id' not in request.session:
        return redirect("login")
    operador = Operadores.objects.get(id=request.session['operador_id'])
    usuarios = Usuario.objects.all()
    total = usuarios.count()
    ativos = usuarios.filter(situacao="Normal").count()
    inativos = usuarios.exclude(situacao="Normal").count()
    return render(request, "usuarios.html", {
        "operador": operador,
        "usuarios": usuarios,
        "total": total,
        "ativos": ativos,
        "inativos": inativos,
    })

def get_db_connection():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, '..', 'database.db')
    db_path = os.path.abspath(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def turmas(request):
    if 'operador_id' not in request.session:
        return redirect("login")
    turmas = Turma.objects.select_related('curso').all().order_by('curso__nome_curso', '-ano')
    cursos = Curso.objects.all()
    total_turmas = turmas.count()
    total_alunos = UsuarioTurma.objects.count()
    return render(request, 'turmas.html', {
        'turmas': turmas,
        'cursos': cursos,
        'total_turmas': total_turmas,
        'total_alunos': total_alunos,
    })

def adicionar_turma(request):
    if request.method == 'POST':
        nome_turma = request.POST.get('nome_turma')
        curso_id = request.POST.get('curso_id')
        ano = request.POST.get('ano')
        turno = request.POST.get('turno')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM app_Turmas WHERE curso_id = ? AND ano = ? AND turno = ?",
            (curso_id, ano, turno)
        )
        (count,) = cursor.fetchone()

        if count > 0:
            cursor.execute("SELECT id, nome_curso FROM app_Cursos")
            cursos = cursor.fetchall()
            conn.close()
            return render(request, 'adicionar_turma.html', {
                'cursos': cursos,
                'error': 'Já existe uma turma para esse curso, ano e turno.'
            })

        cursor.execute(
            "INSERT INTO app_Turmas (nome_turma, curso_id, ano, turno) VALUES (?, ?, ?, ?)",
            (nome_turma, curso_id, ano, turno)
        )
        conn.commit()
        conn.close()
        return redirect('turmas')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_curso FROM app_Cursos")
    cursos = cursor.fetchall()
    conn.close()
    return render(request, 'adicionar_turma.html', {'cursos': cursos})

def deletar_turma(request, turma_id):
    if request.method == 'POST':
        try:
            turma_id = int(turma_id)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM app_Turmas WHERE id = ?", (turma_id,))
            conn.commit()
            conn.close()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'erro', 'mensagem': str(e)}, status=500)
    return JsonResponse({'status': 'erro', 'mensagem': 'Método não permitido'}, status=405)

def registro(request):
    data_selecionada = request.GET.get("data") or now().strftime("%Y-%m-%d")
    logs = LogAcesso.objects.filter(timestamp_acesso__startswith=data_selecionada).select_related('usuario')
    total = logs.count()
    liberados = logs.filter(status="Aceito").count()
    negados = logs.filter(status="Negado").count()
    return render(request, "registro.html", {
        "logs": logs,
        "data_selecionada": data_selecionada,
        "total": total,
        "liberados": liberados,
        "negados": negados,
    })

def permissoes(request):
    if 'operador_id' not in request.session:
        return redirect("login")
    operador = Operadores.objects.get(id=request.session['operador_id'])
    if request.method == "POST":
        form = FormPermissaoEspecial(request.POST)
        if form.is_valid():
            permissao = form.save(commit=False)
            data = form.cleaned_data['data']
            hora = form.cleaned_data['hora']
            from datetime import datetime
            permissao.data_hora_permissao = datetime.combine(data, hora)
            permissao.operador = operador
            permissao.save()
            messages.success(request, "Permissão especial cadastrada com sucesso!")
            return redirect("permissoes")
        else:
            messages.error(request, "Erro ao cadastrar permissão. Verifique os campos.")
    else:
        form = FormPermissaoEspecial()
    permissoes = PermissaoEspecial.objects.select_related('usuario', 'operador').order_by('-data_hora_permissao')
    total = permissoes.count()
    ativas = permissoes.filter(data_hora_permissao__gte=now()).count()
    pendentes = permissoes.filter(data_hora_permissao__gte=now()).count()
    negadas = 0
    return render(request, "permissoes.html", {
        "operador": operador,
        "form": form,
        "permissoes": permissoes,
        "total": total,
        "ativas": ativas,
        "pendentes": pendentes,
        "negadas": negadas,
    })

def buscar_usuario(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse([], safe=False)
    usuarios = Usuario.objects.filter(
        Q(nome_completo__icontains=query) | Q(matricula__icontains=query)
    )[:10]
    resultados = [{"id": u.id, "nome": u.nome_completo, "matricula": u.matricula} for u in usuarios]
    return JsonResponse(resultados, safe=False)

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
    from .models import PermissaoEspecial
    PermissaoEspecial.objects.create(
        usuario_id=usuario_id,
        operador_id=operador_id,
        justificativa=justificativa,
        data_hora_permissao=data_hora
    )
    return JsonResponse({'status': 'ok'})

def listar_permissoes_especiais(request):
    if 'operador_id' not in request.session:
        return JsonResponse({'erro': 'Usuário não autenticado'}, status=401)
    from .models import PermissaoEspecial
    permissoes = PermissaoEspecial.objects.select_related('usuario', 'operador').order_by('-data_hora_permissao')
    lista = [{
        "id": p.id,
        "usuario_nome": p.usuario.nome_completo,
        "matricula": p.usuario.matricula,
        "justificativa": p.justificativa,
        "operador_nome": p.operador.nome,
        "data_hora_permissao": p.data_hora_permissao
    } for p in permissoes]
    return JsonResponse(lista, safe=False)

def suspensoes(request):
    if 'operador_id' not in request.session:
        return redirect("login")
    operador = Operadores.objects.get(id=request.session['operador_id'])
    # Exemplo: buscar suspensões reais se houver model AcaoDisciplinar
    sancoes = []
    try:
        from .models import AcaoDisciplinar
        sancoes = AcaoDisciplinar.objects.filter(tipo="Suspensão").select_related('usuario')
    except Exception:
        pass
    total = len(sancoes)
    ativas = [s for s in sancoes if hasattr(s, 'data_fim') and s.data_fim and s.data_fim >= now().date()]
    return render(request, "suspensoes.html", {
        "operador": operador,
        "sancoes": sancoes,
        "total": total,
        "ativas": len(ativas),
    })

def acessoExterno(request):
    if 'operador_id' not in request.session:
        return redirect("login")
    operador = Operadores.objects.get(id=request.session['operador_id'])
    if request.method == "POST":
        nome = request.POST.get('nome')
        matricula = request.POST.get('matricula')
        tipo = request.POST.get('tipo')
        foto = request.FILES.get('foto')
        if not all([nome, matricula, tipo, foto]):
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect("acessoExterno")
        pasta_destino = os.path.join(settings.BASE_DIR, 'Rostos_cadastrados')
        os.makedirs(pasta_destino, exist_ok=True)
        caminho_foto = os.path.join(pasta_destino, foto.name)
        with open(caminho_foto, 'wb+') as destino:
            for chunk in foto.chunks():
                destino.write(chunk)
        novo_id = cadastrar_usuario(nome, matricula, tipo, foto.name)
        if novo_id:
            messages.success(request, f"Usuário {nome} cadastrado com sucesso!")
        else:
            messages.error(request, f"Erro: matrícula '{matricula}' já cadastrada.")
        return redirect("acessoExterno")
    visitantes = Visitante.objects.all().order_by('-data_cadastro')
    total = visitantes.count()
    hoje = now().date()
    hoje_count = visitantes.filter(horario_programado_inicio__date=hoje).count()
    return render(request, "acessoExterno.html", {
        "operador": operador,
        "visitantes": visitantes,
        "total": total,
        "hoje": hoje_count,
    })

# app/views.py

...

def usuarios(request):
    if 'operador_id' not in request.session:
        return redirect("login")
    operador = Operadores.objects.get(id=request.session['operador_id'])

    # Apenas operadores COAPAC podem acessar esta view
    if operador.papel != "COAPAC":
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("dashboard")

    usuarios = Usuario.objects.all()
    total = usuarios.count()
    ativos = usuarios.filter(situacao="Normal").count()
    inativos = usuarios.exclude(situacao="Normal").count()
    return render(request, "usuarios.html", {
        "operador": operador,
        "usuarios": usuarios,
        "total": total,
        "ativos": ativos,
        "inativos": inativos,
    })

def cadastrar_usuario(request):
    print("--- Início da view cadastrar_usuario ---")
    if 'operador_id' not in request.session:
        return redirect("login")

    operador = Operadores.objects.get(id=request.session['operador_id'])

    if operador.papel != "COAPAC":
        messages.error(request, "Você não tem permissão para cadastrar usuários.")
        return redirect("dashboard")

    if request.method == "POST":
        print("--- Recebida requisição POST ---")
        nome = request.POST.get('nome_completo')
        matricula = request.POST.get('matricula')
        tipo = request.POST.get('tipo')
        foto = request.FILES.get('foto')
        turma_id = request.POST.get('turma_id')

        if not all([nome, matricula, tipo, foto]):
            print("ERRO: Validação falhou, campos obrigatórios não preenchidos.")
            messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
            return redirect("cadastrar_usuario")

        print("Validação OK. Tentando salvar a foto.")
        pasta_destino = os.path.join(settings.BASE_DIR, 'rostos_cadastrados')
        os.makedirs(pasta_destino, exist_ok=True)
        caminho_foto = os.path.join(pasta_destino, foto.name)
        new_filename = foto.name
        
        with open(caminho_foto, 'wb+') as destino:
            for chunk in foto.chunks():
                destino.write(chunk)
        print(f"Foto salva em: {caminho_foto}")

        print("Chamando a função cadastrar_usuario_core...")
        novo_id = cadastrar_usuario_core(nome, matricula, tipo, os.path.join('rostos_cadastrados', new_filename))
        print(f"Retorno de cadastrar_usuario_core: {novo_id}")

        if novo_id:
            print("Cadastro bem-sucedido!")
            messages.success(request, f"Usuário {nome} cadastrado com sucesso!")
        else:
            print("Cadastro falhou. Matrícula pode já existir.")
            messages.error(request, f"Erro ao cadastrar usuário. A matrícula '{matricula}' pode já existir.")

        return redirect("usuarios")

    cursos = Curso.objects.all()
    turmas = Turma.objects.all()
    print("--- Fim da view cadastrar_usuario (GET) ---")
    return render(request, "cadastrar_usuario.html", {
        "cursos": cursos,
        "turmas": turmas,
        "operador": operador,
    })

def turmas(request):
    if 'operador_id' not in request.session:
        return redirect("login")
    turmas = Turma.objects.select_related('curso').all().order_by('curso__nome_curso', '-ano')
    cursos = Curso.objects.all()
    total_turmas = turmas.count()
    total_alunos = UsuarioTurma.objects.count()
    return render(request, 'turmas.html', {
        'turmas': turmas,
        'cursos': cursos,
        'total_turmas': total_turmas,
        'total_alunos': total_alunos,
    })


def adicionar_turma(request):
    if 'operador_id' not in request.session:
        return redirect("login")

    if request.method == 'POST':
        nome_turma = request.POST.get('nome_turma')
        curso_id = request.POST.get('curso_id')
        ano = request.POST.get('ano')
        turno = request.POST.get('turno')
        
        # Lógica de cadastro no banco de dados (usando uma função do core)
        novo_id = criar_turma(nome_turma, curso_id, ano, turno)

        if novo_id:
            messages.success(request, "Turma adicionada com sucesso!")
            return redirect('turmas')
        else:
            messages.error(request, "Falha ao adicionar a turma. Verifique se a turma já existe.")
            return redirect('adicionar_turma')

    cursos = Curso.objects.all()
    return render(request, 'adicionar_turma.html', {'cursos': cursos})

def adicionar_curso(request):
    if 'operador_id' not in request.session:
        return redirect("login")

    if request.method == 'POST':
        nome_curso = request.POST.get('nome_curso')

        if not nome_curso:
            messages.error(request, "O nome do curso não pode ser vazio.")
            return redirect('adicionar_curso')

        try:
            Curso.objects.create(nome_curso=nome_curso)
            messages.success(request, f"Curso '{nome_curso}' adicionado com sucesso!")
            return redirect('turmas')
        except Exception as e:
            messages.error(request, f"Erro ao adicionar curso: {e}")
            return redirect('adicionar_curso')

    return render(request, 'adicionar_curso.html')

def gerenciar_alunos(request, turma_id):
    if 'operador_id' not in request.session:
        return redirect("login")

    turma = get_object_or_404(Turma, id=turma_id)
    
    # Alunos que já estão na turma
    alunos_na_turma = Usuario.objects.filter(usuarioturma__turma=turma)

    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        if usuario_id:
            usuario = get_object_or_404(Usuario, id=usuario_id)
            
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            try:
                # Verifica se o aluno já está na turma usando SQL puro
                c.execute("SELECT COUNT(*) FROM app_UsuarioTurma WHERE usuario_id = ? AND turma_id = ?", (usuario_id, turma_id))
                if c.fetchone()[0] == 0:
                    # Se não existir, insere o novo aluno usando SQL puro
                    c.execute("INSERT INTO app_UsuarioTurma (usuario_id, turma_id) VALUES (?, ?)", (usuario_id, turma_id))
                    conn.commit()
                    messages.success(request, f"Aluno {usuario.nome_completo} adicionado à turma com sucesso!")
                else:
                    messages.warning(request, f"Aluno {usuario.nome_completo} já está nesta turma.")
            except Exception as e:
                conn.rollback()
                messages.error(request, f"Erro no banco de dados ao adicionar aluno: {e}")
            finally:
                conn.close()

        return redirect('gerenciar_alunos', turma_id=turma_id)

    # Alunos disponíveis para serem adicionados
    alunos_disponiveis = Usuario.objects.filter(
        Q(tipo='Discente')
    ).exclude(
        Q(usuarioturma__turma=turma)
    )

    return render(request, 'gerenciar_alunos.html', {
        'turma': turma,
        'alunos_na_turma': alunos_na_turma,
        'alunos_disponiveis': alunos_disponiveis,
    })

def permissoes(request):
    if 'operador_id' not in request.session:
        return redirect("login")
    
    operador = Operadores.objects.get(id=request.session['operador_id'])
    
    if request.method == "POST":
        form = FormPermissaoEspecial(request.POST)
        if form.is_valid():
            permissao = form.save(commit=False)
            data = form.cleaned_data['data']
            hora = form.cleaned_data['hora']
            permissao.data_hora_permissao = datetime.combine(data, hora)
            permissao.operador = operador
            permissao.save()
            messages.success(request, "Permissão especial cadastrada com sucesso!")
            return redirect("permissoes")
        else:
            # O formulário não é válido, exibe os erros
            messages.error(request, "Erro ao cadastrar permissão. Verifique os campos.")
            # A view continuará para o render, exibindo o formulário com os erros
    else:
        form = FormPermissaoEspecial()

    permissoes = PermissaoEspecial.objects.select_related('usuario', 'operador').order_by('-data_hora_permissao')
    total = permissoes.count()
    ativas = permissoes.filter(data_hora_permissao__gte=now()).count()
    pendentes = permissoes.filter(data_hora_permissao__gte=now()).count() # A lógica de pendente é a mesma de ativa
    negadas = 0 # O conceito de negadas não existe diretamente, é mais para a lógica de acesso

    return render(request, "permissoes.html", {
        "operador": operador,
        "form": form,
        "permissoes": permissoes,
        "total": total,
        "ativas": ativas,
        "pendentes": pendentes,
        "negadas": negadas,
    })

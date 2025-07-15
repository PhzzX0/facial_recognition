from django.shortcuts import render, redirect
from .models import Operadores
import hashlib

from django.http import StreamingHttpResponse
import cv2

# Captura da câmera
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def video_feed(request):
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')


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
	
	return render(request, "dashboard.html") # carrega a pagina dashboard 


def usuarios(request):
	if 'operador_id' not in request.session: # verifica se ha um usuario logado
		return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login
	operador = Operadores.objects.get(id=request.session['operador_id']) # variavel para o usuario logado
	
	return render(request, "usuarios.html") # carrega a pagina usuarios


def turmas(request):
	if 'operador_id' not in request.session: # verifica se ha um usuario logado
		return redirect("login") # se nao tiver um usuario logado redireciona para a pagina de login
	operador = Operadores.objects.get(id=request.session['operador_id']) # variavel para o usuario logado

	return render(request, "turmas.html") # carrega a pagina turmas


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



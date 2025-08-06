de django.db importar modelos

# 1. Operadores
classe Operadores(modelos.Modelo): # classe para a tabela operadores
nome = modelos.Campo de Char(comprimento_máximo=150)
login = modelos.Campo de Char(comprimento_máximo=100, único=Verdadeiro)
senha_hash = modelos.Campo de Char(comprimento_máximo=128)
papel = modelos.Campo de Char(comprimento_máximo=50)
data_criacao = modelos.Campo de data e hora(auto_agora_adicionar=Verdadeiro)

# 2. Cursos
classe Curso(modelos.Modelo):
 nome_curso = modelos.Campo de Char(comprimento_máximo=255, único=Verdadeiro)

    classe Meta:
 tabela_db = 'app_Cursos'
 gerenciou = Falso

# 3. Turmas
classe Turma(modelos.Modelo):
 nome_turma = modelos.Campo de Char(comprimento_máximo=255)
 curso = modelos.Chave Estrangeira(Curso, on_delete=modelos.DEFINIR_NULO, nulo=Verdadeiro)
 ano = modelos.Campo Inteiro()
 turno = modelos.Campo de Char(comprimento_máximo=50)

    classe Meta:
 tabela_db = 'app_Turmas'
 gerenciou = Falso

# 4. Usuários
classe Usuário(modelos.Modelo):
 nome_completo = modelos.Campo de Char(comprimento_máximo=255)
 matricula = modelos.Campo de Char(comprimento_máximo=100, único=Verdadeiro, nulo=Verdadeiro)
 tipo = modelos.Campo de Char(comprimento_máximo=20, escolhas=[('Descente', 'Descente'), ('Docente', 'Docente'), ('Servidor', 'Servidor')], nulo=True)
 situação = modelos.Campo de Char(comprimento_máximo=20, escolhas=[('Normal', 'Normal'), ('Advertido', 'Advertido'), ('Suspenso', 'Suspenso')], padrão='Normal')
 caminho_foto_rosto = modelos.Campo de texto()

    classe Meta:
 tabela_db = 'app_Usuários'
 gerenciou = Falso

# 5. UsuarioTurma
classe UsuarioTurma(modelos.Modelo):
 usuário = modelos.Chave Estrangeira(Usuario, on_delete=modelos.CASCATA)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)

    classe Meta:
 tabela_db = 'app_UsuarioTurma'
 único_junto = (('usuário', 'turma'),)
 gerenciou = Falso

# 6. Visitantes
classe Visitante(modelos.Modelo):
 nome_completo = modelos.Campo de Char(comprimento_máximo=255)
 documento = modelos.Campo de Char(comprimento_máximo=100)
 empresa = modelos.Campo de Char(comprimento_máximo=255, nulo=Verdadeiro, em branco=Verdadeiro)
 motivo_acesso = modelos.Campo de texto(nulo=Verdadeiro, em branco=Verdadeiro)
 horario_programado_inicio = modelos.Campo de data e hora(nulo=Verdadeiro, em branco=Verdadeiro)
 horario_programado_fim = modelos.Campo de data e hora(nulo=Verdadeiro, em branco=Verdadeiro)
 data_cadastro = modelos.Campo de data e hora(auto_agora_adicionar=Verdadeiro)

    classe Meta:
 tabela_db = 'app_Visitantes'
 gerenciou = Falso

#7. Logs de Acesso
classe LogAcesso(modelos.Modelo):
 timestamp_acesso = modelos.Campo de texto()
 status = modelos.Campo de Char(comprimento_máximo=20, escolhas=[('Aceito', 'Aceito'), ('Negado', 'Negado'), ('Não Encontrado', 'Não Encontrado')])
 usuário = modelos.Chave Estrangeira(Usuário, nulo=Verdadeiro, em branco=Verdadeiro, on_delete=modelos.SET_NULL)
 visitante = modelos.Chave Estrangeira(Visitante, nulo=Verdadeiro, em branco=Verdadeiro, on_delete=modelos.SET_NULL)
 caminho_foto_capturada = modelos.Campo de texto(nulo=Verdadeiro, em branco=Verdadeiro)
    classe Meta:
 tabela_db = 'app_LogsAcesso'
 gerenciou = Falso

# 8. Ações Disciplinares
classe AcaoDisciplinar(modelos.Modelo):
 usuário = modelos.Chave Estrangeira(Usuario, on_delete=modelos.CASCATA)
 operador = modelos.Chave Estrangeira(Operadores, on_delete=modelos.CASCATA)
 tipo = modelos.Campo de Char(comprimento_máximo=20, escolhas=[('Advertência', 'Advertência'), ('Suspensão', 'Suspensão')])
 motivo = modelos.Campo de texto(nulo=Verdadeiro, em branco=Verdadeiro)
 data_inicio = modelos.Campo de data(nulo=Verdadeiro, em branco=Verdadeiro)
 data_fim = modelos.Campo de data(nulo=Verdadeiro, em branco=Verdadeiro)
 data_registro = modelos.Campo de data e hora(auto_agora_adicionar=Verdadeiro)

    classe Meta:
 tabela_db = 'app_AcoesDisciplinares'
 gerenciou = Falso

# 9. Permissões Especiais
classe PermissãoEspecial(modelos.Modelo):
 usuário = modelos.Chave Estrangeira(Usuario, on_delete=modelos.CASCATA)
 operador = modelos.Chave Estrangeira(Operadores, on_delete=modelos.CASCATA)
 justificativa = modelos.Campo de texto(nulo=Verdadeiro, em branco=Verdadeiro)
 data_hora_permissao = modelos.Campo de data e hora(nulo=Verdadeiro, em branco=Verdadeiro)
 data_criacao = modelos.Campo de data e hora(auto_agora_adicionar=Verdadeiro)

 classe Meta:
 tabela_db = 'app_PermissoesEspeciais'
 gerenciou = Falso

# 10. Liberações COAPAC
classe LiberacaoCOAPAC(modelos.Modelo):
 turma = modelos.Chave Estrangeira(Turma, on_delete=modelos.CASCATA)
 operador = modelos.Chave Estrangeira(Operadores, on_delete=modelos.CASCATA)
 justificativa = modelos.Campo de texto(nulo=Verdadeiro, em branco=Verdadeiro)
 data_liberacao = modelos.Campo de dados(nulo=Verdadeiro, em branco=Verdadeiro)
 horario_liberacao = modelos.Campo de tempo(nulo=Verdadeiro, em branco=Verdadeiro)
 data_registro = modelos.Campo de dados e hora(auto_agora_adicionar=Verdadeiro)

 classe Meta:
 tabela_db = 'app_LiberacoesCOAPAC'
 gerenciou = Falso

# 11. Anúncios
classe Anúncio(modelos.Modelo):
 operador = modelos.Chave Estrangeira(Operadores, on_delete=modelos.CASCATA)
 tipo = modelos.Campo de Char(comentário_máximo=20, escolhas=[('Evento', 'Evento'), ('Lembrete', 'Lembrete')], nulo=True)
 título = modelos.Campo de Char(comentário_máximo=255, nulo=Verdadeiro, em branco=Verdadeiro)
 legenda = modelos.Campo de texto(nulo=Verdadeiro, em branco=Verdadeiro)
 caminho_imagem = modelos.Campo de texto(nulo=Verdadeiro, em branco=Verdadeiro)
 data_inicio_exibicao = modelos.Campo de dados(nulo=Verdadeiro, em branco=Verdadeiro)
 data_fim_exibicao = modelos.Campo de dados(nulo=Verdadeiro, em branco=Verdadeiro)
 data_criacao = modelos.Campo de dados e hora(auto_agora_adicionar=Verdadeiro)

 classe Meta:
 tabela_db = 'app_Anúncios'
 gerenciou = Falso

# 12. Notificações
classe Notificação(modelos.Modelo):
 operador = modelos.Chave Estrangeira(Operadores, on_delete=modelos.CASCATA)
 mensagem = modelos.Campo de texto()
 tipo_alerta = modelos.Campo de texto(nulo=Verdadeiro, em branco=Verdadeiro)
 link_relacionado = modelos.Campo de texto(nulo=Verdadeiro, em branco=Verdadeiro)
 vida = modelos.Campo Booleano(padrão=Falso)
 data_criacao = modelos.Campo de dados e hora(auto_agora_adicionar=Verdadeiro)

 classe Meta:
 tabela_db = 'app_Notificacoes'
 gerenciou = Falso

from django.db import models

#1. operadores
class Operadores(models.Model):
    nome = models.CharField(max_length=150)
    login = models.CharField(max_length=100, unique=True)
    senha_hash = models.CharField(max_length=128)
    papel = models.CharField(max_length=50)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_Operadores'
        managed = False

# 2. Cursos
class Curso(models.Model):
    nome_curso = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'app_Cursos'
        managed = False

# 3. Turmas
class Turma(models.Model):
    nome_turma = models.CharField(max_length=255)
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True)
    ano = models.IntegerField()
    turno = models.CharField(max_length=50)

    class Meta:
        db_table = 'app_Turmas'
        managed = False

# 4. Usuários
class Usuario(models.Model):
    nome_completo = models.CharField(max_length=255)
    matricula = models.CharField(max_length=100, unique=True, null=True)
    tipo = models.CharField(max_length=20, choices=[('Discente', 'Discente'), ('Docente', 'Docente'), ('Servidor', 'Servidor')], null=True)
    situacao = models.CharField(max_length=20, choices=[('Normal', 'Normal'), ('Advertido', 'Advertido'), ('Suspenso', 'Suspenso')], default='Normal')
    caminho_foto_rosto = models.TextField()

    class Meta:
        db_table = 'app_Usuarios'
        managed = False
    def __str__(self):
        return self.nome_completo

# 5. UsuarioTurma
class UsuarioTurma(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)

    class Meta:
        db_table = 'app_UsuarioTurma'
        unique_together = (('usuario', 'turma'),)
        managed = False

# 6. Visitantes
class Visitante(models.Model):
    nome_completo = models.CharField(max_length=255)
    documento = models.CharField(max_length=100)
    empresa = models.CharField(max_length=255, null=True, blank=True)
    motivo_acesso = models.TextField(null=True, blank=True)
    horario_programado_inicio = models.DateTimeField(null=True, blank=True)
    horario_programado_fim = models.DateTimeField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_Visitantes'
        managed = False

#7. Logs de Acesso
class LogAcesso(models.Model):
    timestamp_acesso = models.TextField()
    status = models.CharField(max_length=20, choices=[('Aceito', 'Aceito'), ('Negado', 'Negado'), ('Não Encontrado', 'Não Encontrado')])
    usuario = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL)
    visitante = models.ForeignKey(Visitante, null=True, blank=True, on_delete=models.SET_NULL)
    caminho_foto_capturada = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'app_LogsAcesso'
        managed = False

# 8. Ações Disciplinares
class AcaoDisciplinar(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    operador = models.ForeignKey(Operadores, on_delete=models.CASCADE)
    tipo = models.CharField(
        max_length=20,
        choices=[('Advertência', 'Advertência'), ('Suspensão', 'Suspensão')]
    )
    motivo = models.TextField(null=True, blank=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_AcoesDisciplinares'
        managed = False

    @property
    def nome_usuario(self):
        return self.usuario.nome_completo if self.usuario else None

    @property
    def matricula_usuario(self):
        return self.usuario.matricula if self.usuario else None

# 9. Permissões Especiais
class PermissaoEspecial(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    operador = models.ForeignKey(Operadores, on_delete=models.CASCADE)
    justificativa = models.TextField(null=True, blank=True)
    data_hora_permissao = models.DateTimeField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_PermissoesEspeciais'
        managed = False

# 10. Liberações COAPAC
class LiberacaoCOAPAC(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    operador = models.ForeignKey(Operadores, on_delete=models.CASCADE)
    justificativa = models.TextField(null=True, blank=True)
    data_liberacao = models.DateField(null=True, blank=True)
    horario_liberacao = models.TimeField(null=True, blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_LiberacoesCOAPAC'
        managed = False

# 11. Anúncios
class Anuncio(models.Model):
    operador = models.ForeignKey(Operadores, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=[('Evento', 'Evento'), ('Lembrete', 'Lembrete')], null=True)
    titulo = models.CharField(max_length=255, null=True, blank=True)
    legenda = models.TextField(null=True, blank=True)
    caminho_imagem = models.TextField(null=True, blank=True)
    data_inicio_exibicao = models.DateField(null=True, blank=True)
    data_fim_exibicao = models.DateField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_Anuncios'
        managed = False

# 12. Notificações
class Notificacao(models.Model):
    operador = models.ForeignKey(Operadores, on_delete=models.CASCADE)
    mensagem = models.TextField()
    tipo_alerta = models.TextField(null=True, blank=True)
    link_relacionado = models.TextField(null=True, blank=True)
    lida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_Notificacoes'
        managed = False

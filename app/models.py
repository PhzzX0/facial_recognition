from django.db import models


class Operadores(models.Model): # classe para a tabela operadores
	nome = models.CharField(max_length=150)
	login = models.CharField(max_length=100, unique=True)
	senha_hash = models.CharField(max_length=128)
	papel = models.CharField(max_length=50)
	data_criacao = models.DateTimeField(auto_now_add=True)

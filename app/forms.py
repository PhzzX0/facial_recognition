from django.forms import ModelForm
from django import forms
from .models import (
    Operadores,
    Curso,
    Turma, 
    Usuario, 
    UsuarioTurma, 
    Visitante,
    PermissaoEspecial,
    )

class FormPermissaoEspecial(ModelForm):
    class Meta:
        model = PermissaoEspecial
        fields = ['usuario', 'operador','data_hora_permissao', 'justificativa']
        widgets = {

            'data_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            
        }

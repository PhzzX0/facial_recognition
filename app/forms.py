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

class FormPermissaoEspecial(forms.ModelForm):
    data = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded border px-2 py-1'}), label="Data da Permissão")
    hora = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'w-full rounded border px-2 py-1'}), label="Hora da Permissão")

    class Meta:
        model = PermissaoEspecial
        fields = ['usuario', 'justificativa']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'w-full rounded border px-2 py-1'}),
            'justificativa': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded border px-2 py-1'}),
        }
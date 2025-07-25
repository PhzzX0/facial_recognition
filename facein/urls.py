"""
URL configuration for facein project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('video_feed/', views.video_feed, name='video_feed'),
    path('admin/', admin.site.urls),
    path('', views.index, name="index"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('usuarios/', views.usuarios, name="usuarios"),
    path('turmas/', views.turmas, name="turmas"),
    path('permissoes', views.permissoes, name="permissoes"),
    path('registro/', views.registro, name="registro"),
    path('suspensoes/', views.suspensoes, name="suspensoes"),
    path('acessoExterno/', views.acessoExterno, name="acessoExterno"),
    path('turmas/deletar/<int:turma_id>/', views.deletar_turma, name='deletar_turma'), # View que lida com exclusão de turmas via POST
]

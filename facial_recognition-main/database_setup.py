# Importa bibliotecas necessárias para banco de dados e manipulação de arquivos

# Importa a biblioteca sqlite3 para interagir com o banco de dados SQLite (usada nos logs e verificações de usuários)
import sqlite3
# Importa a biblioteca OS para manipulação de caminhos de arquivos e diretórios (usada para salvar capturas e organizar pastas)
import os
from datetime import datetime, timedelta

def criar_banco_de_dados():
    """
    Cria todas as 12 tabelas necessárias para o sistema se elas não existirem.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'database.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("[DB SETUP] Verificando e criando tabelas...")

    # 1. Tabela de operadores do sistema (admin, porteiro etc)
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_Operadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            papel TEXT NOT NULL CHECK(papel IN ('Administrador', 'Porteiro', 'COAPAC')),
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Cursos disponíveis
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_Cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_curso TEXT NOT NULL UNIQUE
        )
    ''')

    # 3. Turmas associadas aos cursos
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_Turmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_turma TEXT NOT NULL,
            curso_id INTEGER,
            ano INTEGER,
            turno TEXT,
            FOREIGN KEY (curso_id) REFERENCES app_Cursos(id)
        )
    ''')

    # 4. Usuários do sistema (alunos, professores, servidores)
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_Usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            matricula TEXT UNIQUE,
            tipo TEXT CHECK(tipo IN ('Discente', 'Docente', 'Servidor')),
            situacao TEXT DEFAULT 'Normal' CHECK(situacao IN ('Normal', 'Advertido', 'Suspenso')),
            caminho_foto_rosto TEXT NOT NULL
        )
    ''')

    # 5. Relaciona usuários com turmas
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_UsuarioTurma (
            usuario_id INTEGER NOT NULL,
            turma_id INTEGER NOT NULL,
            PRIMARY KEY (usuario_id, turma_id),
            FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (turma_id) REFERENCES Turmas(id) ON DELETE CASCADE
        )
    ''')

    # 6. Visitantes cadastrados no sistema
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_Visitantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            documento TEXT NOT NULL,
            empresa TEXT,
            motivo_acesso TEXT,
            horario_programado_inicio DATETIME,
            horario_programado_fim DATETIME,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 7. Registros de acesso realizados
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_LogsAcesso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_acesso TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Aceito', 'Negado', 'Não Encontrado')),
            usuario_id INTEGER,
            visitante_id INTEGER,
            caminho_foto_capturada TEXT,
            FOREIGN KEY (usuario_id) REFERENCES Usuarios(id),
            FOREIGN KEY (visitante_id) REFERENCES Visitantes(id)
        )
    ''')

    # 8. Registro de ações disciplinares aplicadas
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_AcoesDisciplinares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            operador_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Advertência', 'Suspensão')),
            motivo TEXT,
            data_inicio DATE,
            data_fim DATE,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES Usuarios(id),
            FOREIGN KEY (operador_id) REFERENCES Operadores(id)
        )
    ''')

    # 9. Permissões especiais concedidas
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_PermissoesEspeciais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            operador_id INTEGER NOT NULL,
            justificativa TEXT,
            data_hora_permissao DATETIME,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES Usuarios(id),
            FOREIGN KEY (operador_id) REFERENCES Operadores(id)
        )
    ''')

    # 10. Liberações feitas por COAPAC
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_LiberacoesCOAPAC (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turma_id INTEGER NOT NULL,
            operador_id INTEGER NOT NULL,
            justificativa TEXT,
            data_liberacao DATE,
            horario_liberacao TIME,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (turma_id) REFERENCES Turmas(id),
            FOREIGN KEY (operador_id) REFERENCES Operadores(id)
        )
    ''')

    # 11. Tabela para exibição de anúncios
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_Anuncios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operador_id INTEGER NOT NULL,
            tipo TEXT CHECK(tipo IN ('Evento', 'Lembrete')),
            titulo TEXT,
            legenda TEXT,
            caminho_imagem TEXT,
            data_inicio_exibicao DATE,
            data_fim_exibicao DATE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (operador_id) REFERENCES Operadores(id)
        )
    ''')

    # 12. Notificações geradas no sistema
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_Notificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operador_id INTEGER NOT NULL,
            mensagem TEXT,
            tipo_alerta TEXT,
            link_relacionado TEXT,
            lida BOOLEAN DEFAULT FALSE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (operador_id) REFERENCES Operadores(id)
        )
    ''')

    # Finaliza alterações e fecha a conexão
    conn.commit()
    conn.close()
    print("[DB SETUP] Configuração do banco de dados concluída.")

criar_banco_de_dados()
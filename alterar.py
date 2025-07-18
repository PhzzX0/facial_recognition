import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect('database.db')
c = conn.cursor()


def cadastrar(nome, categoria, curso, advertencia, imagem):
    c.execute('''
    INSERT INTO rostos (nome,)
        VALUES (?, ?, ?, ?, ?)
    ''', (nome, categoria, curso, advertencia, imagem))
    conn.commit()
    conn.close


if __name__ == "__main__":
    while True:
        nome = input('nome: ')
        categoria = input('categoria: ')
        curso = input('curso: ')
        advertencia = input('advertencia: ')
        numero = input('arquivo N°: ')
        arquivo = os.path.join(BASE_DIR, f"pessoa_{numero}.jpg")
        cadastrar(nome, categoria, curso, advertencia, arquivo)
        print("X")
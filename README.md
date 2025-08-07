# [AINDA EM DESENVOLVIMENTO]

## Projeto

Este projeto é um sistema de verificação facial que utiliza uma webcam IP (como o app IP Webcam no Android) para capturar rostos em tempo real, comparar com imagens previamente cadastradas e registrar acessos no banco de dados.


## Instalação

**Desenvolvido com Python 3.12.3**  
*Algumas bibliotecas podem precisar de ajustes dependendo da sua versão.*


1. Clone ou baixe este repositório.
2. Navegue até a pasta do projeto no terminal. (Comando cd)
3. Instale as dependências (**COM BASE NA SUA VERSÃO DO PYTHON; A instalação das bibliotecas tende a ser demorada por conta do peso das bibliotecas de análise facial**):

```bash
pip install -r requirements_3.12.txt
```

4. No celular Android, instale e abra o app [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam).
5. Inicie a câmera no app e pegue o endereço IP mostrado (ex: `http://192.168.18.45:8080/video`).
6. No arquivo `main.py`, na linha que tiver "video_capture = cv2.VideoCapture(0)" coloque o endereço obtido no lugar do zero. (necessário ter o /video no final)

---

## Uso

No terminal, dentro da pasta do projeto, rode o main.py

- Uma janela vai abrir mostrando o vídeo da câmera com rostos detectados.
Quando um rosto for detectado:
   - O sistema capturará a imagem automaticamente.
   - Fará a verificação com os rostos cadastrados.
   - O resultado será exibido no terminal.
- Pressione a tecla `q` para fechar o programa.
- As imagens dos rostos detectados estarão na pasta `rostos/`
- O banco de dados `database.db` terá os registros das imagens salvas com os dados da pessoa cadastrada.

---

## Observações

- A inicialização tende a ter uma pequena demora também, mas nada muito extenso
- Certifique-se de que o celular e o computador estejam conectados na mesma rede Wi-Fi.
- Para melhores resultados, utilize boa iluminação.

---

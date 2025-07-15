## Não entende nada do outro readme? Pois saiba que eu estou aqui para vc OvO

Antes de tudo:
Abra o seu VScode, aperte num icone de 4 quadrados a esquerda e procure e baixe as seguintes extenções: Python e Portuguese (Brasil)..., depois, lá em cima clique em "terminal" e depois "Novo terminal" e digite "python --version", aperte "enter" e veja se sua versão é a 3.12.
Instale o app "IP Webcam"

Como rodar o projeto:
1° No github do projeto, aperte um botão azul escrito "<> Code", após isso aperte em "Download ZIP"
2° Vá para o local onde vc baixou o zip, clique o botão direito nele e aperte a opção "Extract to..."
3° Com O VScode aberto, clique em "arquivo" no canto superior esquerdo, depois em "Abrir pasta..." e selecione a pasta que você extraiu anteriormente
4° Abra um novo terminal e digite nele "pip install -r requirements_3.12.txt", espere até que tudo seja baixado.
Se der um erro vermelho:
   1°: digite no terminal "pip install -–upgrade" para verificar se o seu "pip" está na ultima versão.
   2°: faça os seguintes passos: Pressione Win + R, digite gpedit.msc e pressione Enter. --> Configuração do Computador > Modelos Administrativos > Sistema > Sistema de Arquivos. --> Clique em "Ativar caminhos Win32 longos". --> Marque como "Habilitado" e clique em OK.
5° Abra o aplicativo da câmero no seu celular, aperte nos 3 pontinhos no canto superior direito e depois em "Start server", pegue o ip no canto inferior da tela.
6° No arquivo `main.py`, na linha que tiver "video_capture = cv2.VideoCapture(0)" coloque o endereço obtido no lugar do zero. (necessário ter o /video no final [ex: 'http://192.168.18.45:8080/video'])
7° Estando no arquivo "main.py", aperte no triangulo no canto superior direito para rodar o código.


Se estiver tudo certo deve abrir uma janela espelhando a câmera do seu celular.
Para sair aperte a tecla "q".
Sempre que o programa detectar um "rosto", ele salvarar a imagem em "capturas_log", cuidado com a facilidade de ter dezenas de fotos nessa pasta.

Recomendo agora que leia o outro readme para mais detalhes.
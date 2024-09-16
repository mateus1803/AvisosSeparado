Para implementar os avisos na rede

baixe
- visual studio code
- python 3.12 ou superior

importar pasta do programa para o vs code.

dentro do vscode abrir terminal e importar o Flask 

-   pip install flask
-   pip install Flask-Cors
-   pip install Flask-SocketIO

beleza, feito isso só alterar o ip no server.py no host

e logo em seguida fazer as config nos navegadores para habilitar as notify pelo http

Abra o Google Chrome e acesse chrome://flags/#unsafely-treat-insecure-origin-as-secure 

na barra de endereços.
Ative a opção "Tratar URLs de origem não seguros como seguros" (ou "Insecure origins treated as secure").
Adicione o URL local onde está hospedada a sua aplicação. Por exemplo, http://localhost.
Reinicie o Chrome para que as alterações tenham efeito.
Firefox:

Abra o Firefox e acesse about:config na barra de endereços.
Procure pela configuração

privacy.file_unique_origin          e defina seu valor como false.

Isso permitirá que o Firefox trate as origens de arquivo como não únicas e, portanto, permitirá notificações em ambientes locais.
Você também pode considerar usar uma extensão como o "Web Server for Chrome" para servir seu conteúdo localmente usando HTTPS, o que pode contornar problemas de segurança.
Microsoft Edge:

Abra o Microsoft Edge e acesse edge://flags/#unsafely-treat-insecure-origin-as-secure.
Ative a opção "Tratar URLs de origem não seguros como seguros".
Adicione o URL local da sua aplicação.
Reinicie o Edge para que as alterações tenham efeito.




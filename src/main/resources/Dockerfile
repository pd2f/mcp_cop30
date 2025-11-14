# Versão pareada da imagem completa, com pacotes mínimos necessária para execução do python
FROM docker.io/python:3.12-slim

# Exposto na porta 5005
EXPOSE 5005

# Impede que o container gere arquivos .pyc 
ENV PYTHONDONTWRITEBYTECODE=1

# Desativa o buffer para facilitar o registro de log no container
ENV PYTHONUNBUFFERED=1

# Copia para o diretorio corrente o arquivos de dependências de biblioteca para instalação do pip
COPY /requirements.txt .

# Executa a instalação de dependências no container
RUN python -m pip install -r requirements.txt

#Instalação do pacote TK
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install python3-tk -y

# Define o diretório /app como diretório base de trabalho
WORKDIR /app

#Copia os arquivos do projeto para o diretório base de trabalho
COPY / /app

# Criação de usuário não root e permissão para acessar o diretório /app, assim impedindo que usuário mal intecionados eleve permissões no container.
RUN adduser -u 1409 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Execução do WSGI server no porta 5005

# Assuming you have a file named app.py, with a Shiny app named app.
CMD ["uvicorn","app:app","--host", "0.0.0.0","--port","5005","--ws","websockets"]
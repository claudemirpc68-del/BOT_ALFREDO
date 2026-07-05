FROM python:3.11-slim

# Evita que o Python escreva arquivos .pyc no disco
ENV PYTHONDONTWRITEBYTECODE=1
# Evita que o Python faça buffer do stdout/stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Cria a pasta de dados do banco SQLite
RUN mkdir -p /app/data

# Comando para inicializar o bot
CMD ["python", "run.py"]

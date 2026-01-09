# Usar imagem oficial do Playwright com Python
# Esta imagem já vem com todas as dependências do Chromium instaladas
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Copiar requirements primeiro para aproveitar cache do Docker
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código
COPY . .

# Expor a porta da API
EXPOSE 8000

# Variáveis de ambiente para produção
ENV HEADLESS=True
ENV PYTHONUNBUFFERED=1

# Comando para iniciar a API
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]

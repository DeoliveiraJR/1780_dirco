FROM python:3.11-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar projeto
COPY . .

# Expor porta
EXPOSE 8503

# Comando para rodar Streamlit
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8503", "--server.address=0.0.0.0"]

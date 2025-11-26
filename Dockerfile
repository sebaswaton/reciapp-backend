FROM python:3.9-slim

WORKDIR /code

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app app


# Comando de inicio - usar shell form para expansión de variables
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
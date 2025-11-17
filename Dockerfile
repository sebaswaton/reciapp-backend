FROM python:3.9-slim

WORKDIR /code

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app app

# Definir la variable de entorno con un valor por defecto
ENV DATABASE_URL=""

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
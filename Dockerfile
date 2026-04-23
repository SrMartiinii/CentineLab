# Dockerfile — CentineLab
# Single-stage: suficiente para la fase actual del proyecto.
# TODO: cuando el proyecto crezca, pasar a multi-stage para reducir tamaño.

FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias (capa cacheada mientras no cambie requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY app/ ./app/

# Puerto expuesto por Uvicorn
EXPOSE 8000

# Arranque del servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

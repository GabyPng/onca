# Dockerfile para Backend (src/)
FROM python:3.11-slim

WORKDIR /app

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorio para datos si no existe
RUN mkdir -p ../frontend/static/data

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la API
CMD ["python", "api.py"]

# Dockerfile para Frontend
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para matplotlib
RUN apt-get update && apt-get install -y \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir matplotlib>=3.10.3
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del frontend
COPY . .

# Exponer puerto
EXPOSE 5001

# Comando para ejecutar Flask
CMD ["python", "app.py"]

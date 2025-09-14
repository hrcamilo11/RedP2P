FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorio para archivos compartidos
RUN mkdir -p /app/shared_files

# Exponer puertos (configurables via variables de entorno)
EXPOSE ${PEER_PORT:-8001} ${PEER_GRPC_PORT:-9001}

# Comando de inicio
CMD ["python", "main.py"]

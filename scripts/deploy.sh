#!/bin/bash

# Script de despliegue para el sistema P2P

set -e

echo "=== Desplegando Sistema P2P ==="

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose no está instalado"
    exit 1
fi

# Crear directorios necesarios
echo "Creando directorios..."
mkdir -p shared_files/peer1
mkdir -p shared_files/peer2
mkdir -p shared_files/peer3
mkdir -p central_server_data
mkdir -p logs

# Dar permisos de ejecución a los scripts
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Construir imágenes Docker
echo "Construyendo imágenes Docker..."
docker build -t p2p-peer ./peer
docker build -t central-server ./central_server

# Crear red Docker si no existe
echo "Creando red Docker..."
if ! docker network ls | grep -q p2p-network; then
    docker network create p2p-network --driver bridge --subnet=172.20.0.0/16
    echo "Red p2p-network creada"
else
    echo "Red p2p-network ya existe"
fi

# Detener contenedores existentes si los hay
echo "Deteniendo contenedores existentes..."
docker-compose down 2>/dev/null || true

# Iniciar el sistema
echo "Iniciando sistema P2P..."
docker-compose up -d

# Esperar a que los contenedores se inicien
echo "Esperando a que los peers se inicialicen..."
sleep 10

# Verificar estado de los contenedores
echo "Verificando estado de los contenedores..."
docker-compose ps

# Verificar salud del servidor central
echo "Verificando salud del servidor central..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✓ Servidor central está funcionando"
else
    echo "✗ Servidor central no responde"
fi

# Verificar salud de los peers
echo "Verificando salud de los peers..."
for port in 8001 8002 8003; do
    if curl -s http://localhost:$port/api/health > /dev/null; then
        echo "✓ Peer en puerto $port está funcionando"
    else
        echo "✗ Peer en puerto $port no responde"
    fi
done

echo ""
echo "=== Sistema P2P Desplegado ==="
echo ""
echo "Comandos útiles:"
echo "  - Ver logs: docker-compose logs -f"
echo "  - Detener: docker-compose down"
echo "  - Reiniciar: docker-compose restart"
echo "  - Estado: docker-compose ps"
echo ""
echo "APIs disponibles:"
echo "  - Servidor Central: http://localhost:8000"
echo "  - Peer 1: http://localhost:8001"
echo "  - Peer 2: http://localhost:8002"
echo "  - Peer 3: http://localhost:8003"
echo ""
echo "Para ejecutar pruebas:"
echo "  - Concurrencia: python scripts/test_concurrency.py"
echo "  - Fallos: python scripts/test_failure.py"

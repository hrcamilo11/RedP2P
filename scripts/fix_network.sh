#!/bin/bash

# Script para corregir problemas de red Docker

echo "=== CORRIGIENDO RED DOCKER P2P-NETWORK ==="

# Detener todos los contenedores
echo "Deteniendo contenedores..."
docker-compose down 2>/dev/null

# Eliminar la red existente si existe
echo "Eliminando red existente..."
if docker network ls --format "{{.Name}}" | grep -q "p2p-network"; then
    docker network rm p2p-network 2>/dev/null
    echo "Red p2p-network eliminada"
fi

# Crear la red nuevamente
echo "Creando red p2p-network..."
docker network create p2p-network
if [ $? -eq 0 ]; then
    echo "Red p2p-network creada correctamente"
else
    echo "Error creando red p2p-network"
    exit 1
fi

# Verificar que la red existe
echo "Verificando red..."
docker network ls | grep p2p-network

echo "=== RED CORREGIDA ==="
echo "Ahora puedes ejecutar: ./deploy.sh"

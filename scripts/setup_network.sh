#!/bin/bash

# Script para configurar la red P2P con Docker

echo "=== Configurando Red P2P ==="

# Crear directorios para archivos compartidos
echo "Creando directorios para archivos compartidos..."
mkdir -p shared_files/peer1
mkdir -p shared_files/peer2
mkdir -p shared_files/peer3

# Crear algunos archivos de prueba
echo "Creando archivos de prueba..."
echo "Archivo de prueba 1" > shared_files/peer1/test1.txt
echo "Archivo de prueba 2" > shared_files/peer1/test2.txt
echo "Documento importante" > shared_files/peer2/document.pdf
echo "Imagen de prueba" > shared_files/peer2/image.jpg
echo "Video de muestra" > shared_files/peer3/video.mp4
echo "Código fuente" > shared_files/peer3/source.py

# Crear red Docker
echo "Creando red Docker..."
docker network create p2p-network --driver bridge --subnet=172.20.0.0/16

echo "=== Red P2P configurada correctamente ==="
echo "Para iniciar los peers, ejecuta: docker-compose up"
echo "Para detener los peers, ejecuta: docker-compose down"

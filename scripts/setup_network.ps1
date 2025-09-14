# Script para configurar la red P2P con Docker en Windows

Write-Host "=== Configurando Red P2P ===" -ForegroundColor Green

# Crear directorios para archivos compartidos
Write-Host "Creando directorios para archivos compartidos..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "shared_files\peer1" -Force | Out-Null
New-Item -ItemType Directory -Path "shared_files\peer2" -Force | Out-Null
New-Item -ItemType Directory -Path "shared_files\peer3" -Force | Out-Null
New-Item -ItemType Directory -Path "central_server_data" -Force | Out-Null

# Crear algunos archivos de prueba
Write-Host "Creando archivos de prueba..." -ForegroundColor Yellow
"Archivo de prueba 1" | Out-File -FilePath "shared_files\peer1\test1.txt" -Encoding UTF8
"Archivo de prueba 2" | Out-File -FilePath "shared_files\peer1\test2.txt" -Encoding UTF8
"Documento importante" | Out-File -FilePath "shared_files\peer2\document.pdf" -Encoding UTF8
"Imagen de prueba" | Out-File -FilePath "shared_files\peer2\image.jpg" -Encoding UTF8
"Video de muestra" | Out-File -FilePath "shared_files\peer3\video.mp4" -Encoding UTF8
"Codigo fuente" | Out-File -FilePath "shared_files\peer3\source.py" -Encoding UTF8

# Verificar que Docker esté instalado
Write-Host "Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker encontrado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "Por favor instala Docker Desktop para Windows" -ForegroundColor Red
    exit 1
}

# Crear red Docker
Write-Host "Creando red Docker..." -ForegroundColor Yellow
try {
    $networkExists = docker network ls --filter name=p2p-network --format "{{.Name}}"
    if ($networkExists -eq "p2p-network") {
        Write-Host "✓ Red p2p-network ya existe" -ForegroundColor Green
    } else {
        docker network create p2p-network --driver bridge --subnet=172.20.0.0/16
        Write-Host "✓ Red p2p-network creada" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Error creando red Docker: $_" -ForegroundColor Red
    exit 1
}

Write-Host "=== Red P2P configurada correctamente ===" -ForegroundColor Green
Write-Host "Para iniciar el sistema, ejecuta: .\scripts\deploy.ps1" -ForegroundColor Cyan
Write-Host "Para detener el sistema, ejecuta: docker-compose down" -ForegroundColor Cyan

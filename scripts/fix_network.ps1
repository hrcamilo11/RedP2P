# Script para corregir problemas de red Docker

Write-Host "=== CORRIGIENDO RED DOCKER P2P-NETWORK ===" -ForegroundColor Green

# Detener todos los contenedores
Write-Host "Deteniendo contenedores..." -ForegroundColor Yellow
docker-compose down 2>$null

# Eliminar la red existente si existe
Write-Host "Eliminando red existente..." -ForegroundColor Yellow
$networkExists = docker network ls --format "{{.Name}}" | Where-Object { $_ -eq "p2p-network" }
if ($networkExists) {
    docker network rm p2p-network 2>$null
    Write-Host "Red p2p-network eliminada" -ForegroundColor Green
}

# Crear la red nuevamente
Write-Host "Creando red p2p-network..." -ForegroundColor Yellow
docker network create p2p-network
if ($LASTEXITCODE -eq 0) {
    Write-Host "Red p2p-network creada correctamente" -ForegroundColor Green
} else {
    Write-Host "Error creando red p2p-network" -ForegroundColor Red
    exit 1
}

# Verificar que la red existe
Write-Host "Verificando red..." -ForegroundColor Yellow
docker network ls | findstr p2p-network

Write-Host "=== RED CORREGIDA ===" -ForegroundColor Green
Write-Host "Ahora puedes ejecutar: .\deploy.ps1" -ForegroundColor Cyan

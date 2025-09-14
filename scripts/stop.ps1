# Script para detener el sistema P2P en Windows

Write-Host "=== Deteniendo Sistema P2P ===" -ForegroundColor Yellow

# Verificar si hay contenedores ejecutándose
Write-Host "Verificando contenedores ejecutándose..." -ForegroundColor Yellow
$runningContainers = docker-compose ps --format "{{.Name}}\t{{.Status}}" | Where-Object { $_ -match "Up" }

if (-not $runningContainers) {
    Write-Host "⚠️  No hay contenedores ejecutándose" -ForegroundColor Yellow
    exit 0
}

Write-Host "Contenedores encontrados:" -ForegroundColor Cyan
Write-Host $runningContainers

# Confirmar detención
$response = Read-Host "¿Detener todos los contenedores? (s/N)"
if ($response -ne "s" -and $response -ne "S" -and $response -ne "y" -and $response -ne "Y") {
    Write-Host "Operación cancelada" -ForegroundColor Yellow
    exit 0
}

# Detener contenedores
Write-Host "Deteniendo contenedores..." -ForegroundColor Yellow
try {
    docker-compose down
    Write-Host "✓ Contenedores detenidos" -ForegroundColor Green
} catch {
    Write-Host "✗ Error deteniendo contenedores: $_" -ForegroundColor Red
    exit 1
}

# Verificar que se hayan detenido
Write-Host "Verificando estado..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$remainingContainers = docker-compose ps --format "{{.Name}}\t{{.Status}}" | Where-Object { $_ -match "Up" }
if ($remainingContainers) {
    Write-Host "⚠️  Algunos contenedores siguen ejecutándose:" -ForegroundColor Yellow
    Write-Host $remainingContainers
    Write-Host "Usa 'docker-compose down --remove-orphans' para forzar la detención" -ForegroundColor Cyan
} else {
    Write-Host "✓ Todos los contenedores han sido detenidos" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Sistema P2P Detenido ===" -ForegroundColor Green
Write-Host ""
Write-Host "Para reiniciar el sistema:" -ForegroundColor Cyan
Write-Host "  .\scripts\start.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Para limpiar completamente:" -ForegroundColor Cyan
Write-Host "  .\scripts\cleanup.ps1 -All" -ForegroundColor White

# Script de inicio para Red P2P
# Inicia el sistema completo de compartir archivos P2P

Write-Host "🚀 Iniciando Red P2P - Sistema de Compartir Archivos" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Verificar si Docker está ejecutándose
Write-Host "📋 Verificando Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker está ejecutándose" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está ejecutándose. Por favor inicia Docker Desktop." -ForegroundColor Red
    exit 1
}

# Crear red Docker si no existe
Write-Host "🌐 Configurando red Docker..." -ForegroundColor Yellow
$networkExists = docker network ls --filter name=p2p-network --format "{{.Name}}"
if (-not $networkExists) {
    Write-Host "📡 Creando red p2p-network..." -ForegroundColor Yellow
    docker network create p2p-network
    Write-Host "✅ Red p2p-network creada" -ForegroundColor Green
} else {
    Write-Host "✅ Red p2p-network ya existe" -ForegroundColor Green
}

# Detener contenedores existentes
Write-Host "🛑 Deteniendo contenedores existentes..." -ForegroundColor Yellow
docker-compose down 2>$null

# Construir e iniciar servicios
Write-Host "🔨 Construyendo e iniciando servicios..." -ForegroundColor Yellow
docker-compose up -d --build

# Esperar a que los servicios estén listos
Write-Host "⏳ Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar estado de los servicios
Write-Host "🔍 Verificando estado de los servicios..." -ForegroundColor Yellow
$services = @("p2p-central-server", "p2p-peer-1", "p2p-peer-2", "p2p-peer-3")

foreach ($service in $services) {
    $status = docker ps --filter name=$service --format "{{.Status}}"
    if ($status -like "*Up*") {
        Write-Host "✅ $service está ejecutándose" -ForegroundColor Green
    } else {
        Write-Host "❌ $service no está ejecutándose" -ForegroundColor Red
    }
}

# Mostrar información de acceso
Write-Host "`n🎉 Sistema P2P iniciado correctamente!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "🌐 Interfaz Web: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📊 API Central: http://localhost:8000/api/stats" -ForegroundColor Cyan
Write-Host "👥 Peer 1: http://localhost:8001" -ForegroundColor Cyan
Write-Host "👥 Peer 2: http://localhost:8002" -ForegroundColor Cyan
Write-Host "👥 Peer 3: http://localhost:8003" -ForegroundColor Cyan
Write-Host "`n💡 Usa 'docker-compose logs -f' para ver logs en tiempo real" -ForegroundColor Yellow
Write-Host "🛑 Usa 'docker-compose down' para detener el sistema" -ForegroundColor Yellow

# Abrir interfaz web
Write-Host "`n🌐 Abriendo interfaz web..." -ForegroundColor Yellow
Start-Process "http://localhost:8000"
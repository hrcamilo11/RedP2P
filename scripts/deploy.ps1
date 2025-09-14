# Script de despliegue para el sistema P2P en Windows

param(
    [switch]$Build,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Status
)

Write-Host "=== Desplegando Sistema P2P ===" -ForegroundColor Green

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

# Verificar que Docker Compose esté instalado
Write-Host "Verificando Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose encontrado: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose no está instalado" -ForegroundColor Red
    Write-Host "Por favor instala Docker Compose" -ForegroundColor Red
    exit 1
}

# Crear directorios necesarios
Write-Host "Creando directorios..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "shared_files\peer1" -Force | Out-Null
New-Item -ItemType Directory -Path "shared_files\peer2" -Force | Out-Null
New-Item -ItemType Directory -Path "shared_files\peer3" -Force | Out-Null
New-Item -ItemType Directory -Path "central_server_data" -Force | Out-Null
New-Item -ItemType Directory -Path "logs" -Force | Out-Null

# Dar permisos de ejecución a los scripts
Write-Host "Configurando permisos de scripts..." -ForegroundColor Yellow
Get-ChildItem -Path "scripts\*.ps1" | ForEach-Object {
    if ((Get-ExecutionPolicy) -eq "Restricted") {
        Write-Host "⚠️  Política de ejecución restringida. Ejecuta como administrador:" -ForegroundColor Yellow
        Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
    }
}

# Manejar parámetros
if ($Stop) {
    Write-Host "Deteniendo contenedores..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✓ Contenedores detenidos" -ForegroundColor Green
    exit 0
}

if ($Status) {
    Write-Host "Estado de los contenedores:" -ForegroundColor Yellow
    docker-compose ps
    exit 0
}

if ($Restart) {
    Write-Host "Reiniciando contenedores..." -ForegroundColor Yellow
    docker-compose restart
    Write-Host "✓ Contenedores reiniciados" -ForegroundColor Green
    exit 0
}

# Construir imágenes Docker
if ($Build -or $true) {
    Write-Host "Construyendo imágenes Docker..." -ForegroundColor Yellow
    try {
        docker build -t p2p-peer ./peer
        Write-Host "✓ Imagen p2p-peer construida" -ForegroundColor Green
        
        docker build -t central-server ./central_server
        Write-Host "✓ Imagen central-server construida" -ForegroundColor Green
    } catch {
        Write-Host "✗ Error construyendo imágenes: $_" -ForegroundColor Red
        exit 1
    }
}

# Crear red Docker si no existe
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

# Detener contenedores existentes si los hay
Write-Host "Deteniendo contenedores existentes..." -ForegroundColor Yellow
docker-compose down 2>$null

# Iniciar el sistema
Write-Host "Iniciando sistema P2P..." -ForegroundColor Yellow
try {
    docker-compose up -d
    Write-Host "✓ Sistema P2P iniciado" -ForegroundColor Green
} catch {
    Write-Host "✗ Error iniciando sistema: $_" -ForegroundColor Red
    exit 1
}

# Esperar a que los contenedores se inicien
Write-Host "Esperando a que los contenedores se inicialicen..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Verificar estado de los contenedores
Write-Host "Verificando estado de los contenedores..." -ForegroundColor Yellow
docker-compose ps

# Verificar salud del servidor central
Write-Host "Verificando salud del servidor central..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Servidor central está funcionando" -ForegroundColor Green
    } else {
        Write-Host "✗ Servidor central no responde (HTTP $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Servidor central no responde: $_" -ForegroundColor Red
}

# Verificar salud de los peers
Write-Host "Verificando salud de los peers..." -ForegroundColor Yellow
$ports = @(8001, 8002, 8003)
foreach ($port in $ports) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port/api/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Peer en puerto $port está funcionando" -ForegroundColor Green
        } else {
            Write-Host "✗ Peer en puerto $port no responde (HTTP $($response.StatusCode))" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Peer en puerto $port no responde: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Sistema P2P Desplegado ===" -ForegroundColor Green
Write-Host ""
Write-Host "Comandos útiles:" -ForegroundColor Cyan
Write-Host "  - Ver logs: docker-compose logs -f" -ForegroundColor White
Write-Host "  - Detener: .\scripts\deploy.ps1 -Stop" -ForegroundColor White
Write-Host "  - Reiniciar: .\scripts\deploy.ps1 -Restart" -ForegroundColor White
Write-Host "  - Estado: .\scripts\deploy.ps1 -Status" -ForegroundColor White
Write-Host "  - Reconstruir: .\scripts\deploy.ps1 -Build" -ForegroundColor White
Write-Host ""
Write-Host "APIs disponibles:" -ForegroundColor Cyan
Write-Host "  - Servidor Central: http://localhost:8000" -ForegroundColor White
Write-Host "  - Peer 1: http://localhost:8001" -ForegroundColor White
Write-Host "  - Peer 2: http://localhost:8002" -ForegroundColor White
Write-Host "  - Peer 3: http://localhost:8003" -ForegroundColor White
Write-Host ""
Write-Host "Para ejecutar pruebas:" -ForegroundColor Cyan
Write-Host "  - Concurrencia: python scripts\test_concurrency.py" -ForegroundColor White
Write-Host "  - Fallos: python scripts\test_failure.py" -ForegroundColor White
Write-Host "  - Servidor Central: python scripts\test_central_server.py" -ForegroundColor White
Write-Host "  - Demostración: python examples\demo_central_server.py" -ForegroundColor White

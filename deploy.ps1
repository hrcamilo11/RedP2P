# Script de despliegue completo para RedP2P
# Realiza una instalación limpia de todos los servicios y abre la interfaz web

param(
    [switch]$SkipCleanup,
    [switch]$SkipBuild,
    [switch]$SkipTests,
    [string]$Browser = "default"
)

# Configuración
$ProjectName = "RedP2P"
$CentralServerUrl = "http://localhost:8000"
$NetworkName = "p2p-network"
$Timeout = 60

# Colores para output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = ""
    )
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Prefix$Message" -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor $Colors.Header
    Write-Host "  $Title" -ForegroundColor $Colors.Header
    Write-Host "=" * 60 -ForegroundColor $Colors.Header
    Write-Host ""
}

function Write-Step {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Message
    )
    Write-ColorOutput "Paso $Step/$Total - $Message" $Colors.Info "🔧 "
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Wait-ForService {
    param(
        [string]$Url,
        [string]$ServiceName,
        [int]$MaxWait = 60
    )
    
    Write-ColorOutput "Esperando que $ServiceName esté disponible..." $Colors.Info "⏳ "
    
    $elapsed = 0
    while ($elapsed -lt $MaxWait) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "$ServiceName está disponible" $Colors.Success "✅ "
                return $true
            }
        } catch {
            # Servicio aún no disponible
        }
        
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Progress -Activity "Esperando $ServiceName" -Status "Tiempo transcurrido: $elapsed segundos" -PercentComplete (($elapsed / $MaxWait) * 100)
    }
    
    Write-Progress -Activity "Esperando $ServiceName" -Completed
    Write-ColorOutput "$ServiceName no está disponible después de $MaxWait segundos" $Colors.Error "❌ "
    return $false
}

function Open-Browser {
    param([string]$Url)
    
    Write-ColorOutput "Abriendo interfaz web en el navegador..." $Colors.Info "🌐 "
    
    try {
        switch ($Browser.ToLower()) {
            "chrome" { Start-Process "chrome" $Url }
            "firefox" { Start-Process "firefox" $Url }
            "edge" { Start-Process "msedge" $Url }
            "default" { Start-Process $Url }
            default { Start-Process $Url }
        }
        Write-ColorOutput "Navegador abierto en $Url" $Colors.Success "✅ "
    } catch {
        Write-ColorOutput "No se pudo abrir el navegador automáticamente" $Colors.Warning "⚠️ "
        Write-ColorOutput "Abra manualmente: $Url" $Colors.Info "💡 "
    }
}

# Inicio del script
Write-Header "🚀 DESPLIEGUE COMPLETO DE $ProjectName"

# Verificar prerrequisitos
Write-Step 1 9 "Verificando prerrequisitos..."

$prerequisites = @{
    "Docker" = Test-Command "docker"
    "Docker Compose" = Test-Command "docker-compose"
}

$missingPrereqs = @()
foreach ($prereq in $prerequisites.GetEnumerator()) {
    if ($prereq.Value) {
        Write-ColorOutput "$($prereq.Key) está instalado" $Colors.Success "✅ "
    } else {
        Write-ColorOutput "$($prereq.Key) NO está instalado" $Colors.Error "❌ "
        $missingPrereqs += $prereq.Key
    }
}

if ($missingPrereqs.Count -gt 0) {
    Write-ColorOutput "Prerrequisitos faltantes: $($missingPrereqs -join ', ')" $Colors.Error "❌ "
    Write-ColorOutput "Instale los prerrequisitos antes de continuar" $Colors.Error "❌ "
    exit 1
}

# Limpiar instalación anterior
if (-not $SkipCleanup) {
    Write-Step 2 9 "Limpiando instalación anterior..."
    
    Write-ColorOutput "Deteniendo contenedores existentes..." $Colors.Info "🛑 "
    docker-compose down --remove-orphans 2>$null
    
    Write-ColorOutput "Eliminando contenedores huérfanos..." $Colors.Info "🗑️ "
    docker container prune -f 2>$null
    
    Write-ColorOutput "Eliminando imágenes no utilizadas..." $Colors.Info "🗑️ "
    docker image prune -f 2>$null
    
    Write-ColorOutput "Limpieza completada" $Colors.Success "✅ "
} else {
    Write-ColorOutput "Saltando limpieza (--SkipCleanup especificado)" $Colors.Warning "⚠️ "
}

# Configurar red Docker (manejada automáticamente por Docker Compose)
Write-Step 3 9 "Configurando red Docker..."

Write-ColorOutput "La red '$NetworkName' será creada automáticamente por Docker Compose" $Colors.Info "ℹ️ "

# Crear directorios necesarios
Write-Step 4 9 "Creando estructura de directorios..."

$directories = @(
    "data/central-server",
    "data/shared-files/peer1",
    "data/shared-files/peer2", 
    "data/shared-files/peer3",
    "config"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-ColorOutput "Directorio '$dir' creado" $Colors.Success "📁 "
    } else {
        Write-ColorOutput "Directorio '$dir' ya existe" $Colors.Info "ℹ️ "
    }
}

# Construir imágenes
if (-not $SkipBuild) {
    Write-Step 5 9 "Construyendo imágenes Docker..."
    
    Write-ColorOutput "Construyendo imagen del servidor central..." $Colors.Info "🔨 "
    docker-compose build central-server
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Error construyendo servidor central" $Colors.Error "❌ "
        exit 1
    }
    
    Write-ColorOutput "Construyendo imagen de nodos peer..." $Colors.Info "🔨 "
    docker-compose build peer-node-1 peer-node-2 peer-node-3
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Error construyendo nodos peer" $Colors.Error "❌ "
        exit 1
    }
    
    Write-ColorOutput "Imágenes construidas correctamente" $Colors.Success "✅ "
} else {
    Write-ColorOutput "Saltando construcción (--SkipBuild especificado)" $Colors.Warning "⚠️ "
}

# Recrear base de datos
Write-Step 6 9 "Recreando base de datos..."

# Ejecutar dentro del contenedor para usar dependencias (SQLAlchemy)
$dbUrl = "sqlite:///./data/central_server.db"

Write-ColorOutput "Ejecutando creación de tablas dentro del contenedor..." $Colors.Info "🗄️ "
$args = @(
    "run",
    "--rm",
    "-e", "DATABASE_URL=$dbUrl",
    "central-server",
    "python", "/app/init_db.py"
)

$proc = Start-Process -FilePath "docker-compose" -ArgumentList $args -NoNewWindow -PassThru -Wait

if ($proc.ExitCode -ne 0) {
    Write-ColorOutput "Error recreando base de datos (docker-compose run)" $Colors.Error "❌ "
    exit 1
}

Write-ColorOutput "Base de datos recreada correctamente" $Colors.Success "✅ "

# Iniciar servicios
Write-Step 7 9 "Iniciando servicios..."

Write-ColorOutput "Iniciando servidor central..." $Colors.Info "🚀 "
docker-compose up -d central-server
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "Error iniciando servidor central" $Colors.Error "❌ "
    exit 1
}

# Esperar a que el servidor central esté disponible
if (-not (Wait-ForService "$CentralServerUrl/api/health" "Servidor Central" $Timeout)) {
    Write-ColorOutput "El servidor central no está respondiendo" $Colors.Error "❌ "
    Write-ColorOutput "Revisando logs del servidor central..." $Colors.Info "📋 "
    docker logs p2p-central-server --tail 20
    exit 1
}

Write-ColorOutput "Iniciando nodos peer..." $Colors.Info "🚀 "
docker-compose up -d peer-node-1 peer-node-2 peer-node-3
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "Error iniciando nodos peer" $Colors.Error "❌ "
    exit 1
}

# Esperar a que los peers se registren
Write-ColorOutput "Esperando que los peers se registren..." $Colors.Info "⏳ "
Start-Sleep -Seconds 10

# Verificar estado de los servicios
Write-Step 8 9 "Verificando estado de los servicios..."

$services = @(
    @{Name="Servidor Central"; Container="p2p-central-server"; Port=8000},
    @{Name="Peer 1"; Container="p2p-peer-1"; Port=8001},
    @{Name="Peer 2"; Container="p2p-peer-2"; Port=8002},
    @{Name="Peer 3"; Container="p2p-peer-3"; Port=8003}
)

$allServicesRunning = $true
foreach ($service in $services) {
    $containerStatus = docker inspect $service.Container --format "{{.State.Status}}" 2>$null
    if ($containerStatus -eq "running") {
        Write-ColorOutput "$($service.Name) está ejecutándose" $Colors.Success "✅ "
    } else {
        Write-ColorOutput "$($service.Name) NO está ejecutándose (Estado: $containerStatus)" $Colors.Error "❌ "
        $allServicesRunning = $false
    }
}

if (-not $allServicesRunning) {
    Write-ColorOutput "Algunos servicios no están ejecutándose correctamente" $Colors.Error "❌ "
    Write-ColorOutput "Revisando logs..." $Colors.Info "📋 "
    docker-compose logs --tail 10
    exit 1
}

# Ejecutar pruebas
if (-not $SkipTests) {
    Write-Step 9 9 "Ejecutando pruebas del sistema..."
    
    $testScript = Join-Path $PSScriptRoot "scripts\test_web_interface.ps1"
    if (Test-Path $testScript) {
        Write-ColorOutput "Ejecutando pruebas de la interfaz web..." $Colors.Info "🧪 "
        & $testScript -ServerUrl $CentralServerUrl -Timeout 30
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Pruebas completadas exitosamente" $Colors.Success "✅ "
        } else {
            Write-ColorOutput "Algunas pruebas fallaron" $Colors.Warning "⚠️ "
        }
    } else {
        Write-ColorOutput "Script de pruebas no encontrado, saltando..." $Colors.Warning "⚠️ "
    }
} else {
    Write-ColorOutput "Saltando pruebas (--SkipTests especificado)" $Colors.Warning "⚠️ "
}

# Mostrar información del sistema
Write-Header "📊 INFORMACIÓN DEL SISTEMA"

Write-ColorOutput "Servicios desplegados:" $Colors.Info "ℹ️ "
Write-ColorOutput "  • Servidor Central: $CentralServerUrl" $Colors.Success "🌐 "
Write-ColorOutput "  • Peer 1: http://localhost:8001" $Colors.Success "🌐 "
Write-ColorOutput "  • Peer 2: http://localhost:8002" $Colors.Success "🌐 "
Write-ColorOutput "  • Peer 3: http://localhost:8003" $Colors.Success "🌐 "

Write-ColorOutput "`nComandos útiles:" $Colors.Info "ℹ️ "
Write-ColorOutput "  • Ver logs: docker-compose logs -f" $Colors.Info "📋 "
Write-ColorOutput "  • Detener: docker-compose down" $Colors.Info "🛑 "
Write-ColorOutput "  • Reiniciar: docker-compose restart" $Colors.Info "🔄 "
Write-ColorOutput "  • Estado: docker-compose ps" $Colors.Info "📊 "

# Abrir interfaz web
Write-Header "🌐 ABRIENDO INTERFAZ WEB"

Open-Browser $CentralServerUrl

# Esperar un momento para que el navegador se abra
Start-Sleep -Seconds 2

Write-Header "🎉 DESPLIEGUE COMPLETADO"

Write-ColorOutput "¡RedP2P ha sido desplegado exitosamente!" $Colors.Success "🎉 "
Write-ColorOutput "La interfaz web debería abrirse automáticamente en tu navegador" $Colors.Success "🌐 "
Write-ColorOutput "Si no se abre, visita manualmente: $CentralServerUrl" $Colors.Info "💡 "

Write-ColorOutput "`nPara detener el sistema, ejecuta:" $Colors.Info "ℹ️ "
Write-ColorOutput "  docker-compose down" $Colors.Warning "⚠️ "

Write-ColorOutput "`n¡Disfruta usando RedP2P! 🚀" $Colors.Success "✨ "

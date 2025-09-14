# Script de prueba para la interfaz web de RedP2P
# Ejecuta pruebas automatizadas de la interfaz web

param(
    [string]$ServerUrl = "http://localhost:8000",
    [int]$Timeout = 10
)

Write-Host "🚀 Iniciando pruebas de la interfaz web RedP2P" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

# Verificar que Python esté disponible
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no encontrado. Instale Python para ejecutar las pruebas." -ForegroundColor Red
    exit 1
}

# Verificar que el servidor esté ejecutándose
Write-Host "`n🔍 Verificando que el servidor esté ejecutándose..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$ServerUrl/api/health" -TimeoutSec $Timeout -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Servidor respondiendo correctamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Servidor respondió con código: $($response.StatusCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ No se pudo conectar al servidor en $ServerUrl" -ForegroundColor Red
    Write-Host "   Asegúrese de que el servidor central esté ejecutándose:" -ForegroundColor Yellow
    Write-Host "   docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

# Ejecutar pruebas con Python
Write-Host "`n🔍 Ejecutando pruebas automatizadas..." -ForegroundColor Yellow
try {
    $scriptPath = Join-Path $PSScriptRoot "test_web_interface.py"
    $result = python $scriptPath --url $ServerUrl --timeout $Timeout
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 ¡Todas las pruebas pasaron!" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️ Algunas pruebas fallaron" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error ejecutando pruebas: $_" -ForegroundColor Red
    exit 1
}

# Pruebas adicionales con PowerShell
Write-Host "`n🔍 Ejecutando pruebas adicionales con PowerShell..." -ForegroundColor Yellow

# Probar archivos estáticos
$staticFiles = @(
    "/",
    "/static/index.html",
    "/static/styles.css",
    "/static/app.js"
)

$staticTestsPassed = 0
foreach ($file in $staticFiles) {
    try {
        $response = Invoke-WebRequest -Uri "$ServerUrl$file" -TimeoutSec $Timeout -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $file - OK" -ForegroundColor Green
            $staticTestsPassed++
        } else {
            Write-Host "❌ $file - Error $($response.StatusCode)" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $file - Error: $_" -ForegroundColor Red
    }
}

# Probar endpoints de API
Write-Host "`n🔍 Probando endpoints de API..." -ForegroundColor Yellow
$apiEndpoints = @(
    @{Method="GET"; Path="/api/stats"; Name="Estadísticas"},
    @{Method="GET"; Path="/api/peers"; Name="Lista de peers"},
    @{Method="GET"; Path="/api/peers/online"; Name="Peers online"},
    @{Method="GET"; Path="/api/transfers/active"; Name="Transferencias activas"}
)

$apiTestsPassed = 0
foreach ($endpoint in $apiEndpoints) {
    try {
        $response = Invoke-WebRequest -Uri "$ServerUrl$($endpoint.Path)" -Method $endpoint.Method -TimeoutSec $Timeout -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($endpoint.Name) - OK" -ForegroundColor Green
            $apiTestsPassed++
        } else {
            Write-Host "❌ $($endpoint.Name) - Error $($response.StatusCode)" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $($endpoint.Name) - Error: $_" -ForegroundColor Red
    }
}

# Resumen final
Write-Host "`n" + "=" * 50 -ForegroundColor Cyan
Write-Host "📊 Resumen de pruebas PowerShell:" -ForegroundColor Yellow
Write-Host "   ✅ Archivos estáticos: $staticTestsPassed/$($staticFiles.Count)" -ForegroundColor $(if($staticTestsPassed -eq $staticFiles.Count) {"Green"} else {"Yellow"})
Write-Host "   ✅ Endpoints API: $apiTestsPassed/$($apiEndpoints.Count)" -ForegroundColor $(if($apiTestsPassed -eq $apiEndpoints.Count) {"Green"} else {"Yellow"})

# Abrir navegador si las pruebas pasaron
if ($LASTEXITCODE -eq 0 -and $staticTestsPassed -eq $staticFiles.Count) {
    Write-Host "`n🌐 Abriendo interfaz web en el navegador..." -ForegroundColor Green
    try {
        Start-Process $ServerUrl
        Write-Host "✅ Navegador abierto en $ServerUrl" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ No se pudo abrir el navegador automáticamente" -ForegroundColor Yellow
        Write-Host "   Abra manualmente: $ServerUrl" -ForegroundColor Yellow
    }
}

Write-Host "`n✨ Pruebas completadas" -ForegroundColor Green

# Script para probar el sistema P2P completo en Windows

param(
    [switch]$Concurrency,
    [switch]$Failure,
    [switch]$Central,
    [switch]$Demo,
    [switch]$All
)

Write-Host "=== Pruebas del Sistema P2P ===" -ForegroundColor Green

# Verificar que Python esté instalado
Write-Host "Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "Por favor instala Python 3.8 o superior" -ForegroundColor Red
    exit 1
}

# Verificar que los contenedores estén ejecutándose
Write-Host "Verificando estado del sistema..." -ForegroundColor Yellow
try {
    $containers = docker-compose ps --format "table {{.Name}}\t{{.Status}}"
    Write-Host $containers
} catch {
    Write-Host "✗ Error verificando contenedores: $_" -ForegroundColor Red
    Write-Host "Asegúrate de que el sistema esté desplegado: .\scripts\deploy.ps1" -ForegroundColor Yellow
    exit 1
}

# Función para ejecutar prueba
function Invoke-Test {
    param(
        [string]$TestName,
        [string]$ScriptPath,
        [string]$Description
    )
    
    Write-Host ""
    Write-Host "=== Ejecutando: $TestName ===" -ForegroundColor Cyan
    Write-Host $Description -ForegroundColor Gray
    
    try {
        $process = Start-Process -FilePath "python" -ArgumentList $ScriptPath -Wait -PassThru -NoNewWindow
        if ($process.ExitCode -eq 0) {
            Write-Host "✓ $TestName completado exitosamente" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ $TestName falló con código $($process.ExitCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ Error ejecutando $TestName : $_" -ForegroundColor Red
        return $false
    }
}

# Ejecutar pruebas según parámetros
$results = @()

if ($All -or $Concurrency) {
    $result = Invoke-Test -TestName "Pruebas de Concurrencia" -ScriptPath "scripts\test_concurrency.py" -Description "Simula múltiples clientes consultando simultáneamente"
    $results += @{Name="Concurrencia"; Result=$result}
}

if ($All -or $Failure) {
    $result = Invoke-Test -TestName "Pruebas de Fallos" -ScriptPath "scripts\test_failure.py" -Description "Simula fallos de contenedores y verifica recuperación"
    $results += @{Name="Fallos"; Result=$result}
}

if ($All -or $Central) {
    $result = Invoke-Test -TestName "Pruebas del Servidor Central" -ScriptPath "scripts\test_central_server.py" -Description "Prueba funcionalidades del servidor central"
    $results += @{Name="Servidor Central"; Result=$result}
}

if ($All -or $Demo) {
    $result = Invoke-Test -TestName "Demostración del Sistema" -ScriptPath "examples\demo_central_server.py" -Description "Demuestra las funcionalidades del sistema completo"
    $results += @{Name="Demostración"; Result=$result}
}

# Si no se especificó ningún parámetro, ejecutar todas las pruebas
if (-not ($Concurrency -or $Failure -or $Central -or $Demo -or $All)) {
    Write-Host "Ejecutando todas las pruebas..." -ForegroundColor Yellow
    
    $result = Invoke-Test -TestName "Pruebas de Concurrencia" -ScriptPath "scripts\test_concurrency.py" -Description "Simula múltiples clientes consultando simultáneamente"
    $results += @{Name="Concurrencia"; Result=$result}
    
    $result = Invoke-Test -TestName "Pruebas de Fallos" -ScriptPath "scripts\test_failure.py" -Description "Simula fallos de contenedores y verifica recuperación"
    $results += @{Name="Fallos"; Result=$result}
    
    $result = Invoke-Test -TestName "Pruebas del Servidor Central" -ScriptPath "scripts\test_central_server.py" -Description "Prueba funcionalidades del servidor central"
    $results += @{Name="Servidor Central"; Result=$result}
    
    $result = Invoke-Test -TestName "Demostración del Sistema" -ScriptPath "examples\demo_central_server.py" -Description "Demuestra las funcionalidades del sistema completo"
    $results += @{Name="Demostración"; Result=$result}
}

# Resumen de resultados
Write-Host ""
Write-Host "=== RESUMEN DE PRUEBAS ===" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

$passed = 0
$total = $results.Count

foreach ($test in $results) {
    $status = if ($test.Result) { "✓ PASS" } else { "✗ FAIL" }
    $color = if ($test.Result) { "Green" } else { "Red" }
    Write-Host "$status - $($test.Name)" -ForegroundColor $color
    
    if ($test.Result) { $passed++ }
}

Write-Host ""
Write-Host "Total: $passed/$total pruebas pasaron" -ForegroundColor Cyan

if ($passed -eq $total) {
    Write-Host "🎉 ¡Todas las pruebas pasaron!" -ForegroundColor Green
} elseif ($passed -ge ($total * 0.8)) {
    Write-Host "⚠️  La mayoría de las pruebas pasaron" -ForegroundColor Yellow
} else {
    Write-Host "❌ Muchas pruebas fallaron" -ForegroundColor Red
}

Write-Host ""
Write-Host "Para más información sobre las pruebas:" -ForegroundColor Cyan
Write-Host "  - Ver logs: docker-compose logs -f" -ForegroundColor White
Write-Host "  - Estado del sistema: .\scripts\deploy.ps1 -Status" -ForegroundColor White
Write-Host "  - Reiniciar sistema: .\scripts\deploy.ps1 -Restart" -ForegroundColor White

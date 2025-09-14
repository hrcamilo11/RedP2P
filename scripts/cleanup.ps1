# Script de limpieza para Red P2P
# Limpia contenedores, volúmenes y redes del sistema P2P

Write-Host "🧹 Limpiando Red P2P - Sistema de Compartir Archivos" -ForegroundColor Red
Write-Host "=================================================" -ForegroundColor Red

# Detener y eliminar contenedores
Write-Host "🛑 Deteniendo contenedores..." -ForegroundColor Yellow
docker-compose down

# Eliminar contenedores específicos del proyecto
Write-Host "🗑️ Eliminando contenedores del proyecto..." -ForegroundColor Yellow
$containers = @("p2p-central-server", "p2p-peer-1", "p2p-peer-2", "p2p-peer-3")
foreach ($container in $containers) {
    if (docker ps -a --filter name=$container --format "{{.Names}}" | Select-String $container) {
        Write-Host "   Eliminando $container..." -ForegroundColor Yellow
        docker rm -f $container 2>$null
    }
}

# Eliminar imágenes del proyecto
Write-Host "🖼️ Eliminando imágenes del proyecto..." -ForegroundColor Yellow
$images = @("redp2p-central-server", "redp2p-peer1", "redp2p-peer2", "redp2p-peer3")
foreach ($image in $images) {
    if (docker images --filter reference=$image --format "{{.Repository}}" | Select-String $image) {
        Write-Host "   Eliminando imagen $image..." -ForegroundColor Yellow
        docker rmi -f $image 2>$null
    }
}

# Eliminar red si existe
Write-Host "🌐 Eliminando red p2p-network..." -ForegroundColor Yellow
if (docker network ls --filter name=p2p-network --format "{{.Name}}" | Select-String "p2p-network") {
    docker network rm p2p-network
    Write-Host "✅ Red p2p-network eliminada" -ForegroundColor Green
} else {
    Write-Host "ℹ️ Red p2p-network no existe" -ForegroundColor Blue
}

# Limpiar volúmenes huérfanos
Write-Host "📦 Limpiando volúmenes huérfanos..." -ForegroundColor Yellow
docker volume prune -f

# Limpiar imágenes huérfanas
Write-Host "🖼️ Limpiando imágenes huérfanas..." -ForegroundColor Yellow
docker image prune -f

Write-Host "`n✅ Limpieza completada!" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green
Write-Host "🎯 Todos los contenedores, imágenes y redes del proyecto han sido eliminados" -ForegroundColor Cyan
Write-Host "💾 Los datos en ./data/ se mantienen intactos" -ForegroundColor Cyan
Write-Host "`n💡 Para reiniciar el sistema, ejecuta: .\scripts\start.ps1" -ForegroundColor Yellow
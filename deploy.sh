#!/bin/bash

# Script de despliegue completo para RedP2P
# Realiza una instalación limpia de todos los servicios y abre la interfaz web

# Configuración
PROJECT_NAME="RedP2P"
CENTRAL_SERVER_URL="http://localhost:8000"
NETWORK_NAME="p2p-network"
TIMEOUT=60

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parámetros
SKIP_CLEANUP=false
SKIP_BUILD=false
SKIP_TESTS=false
BROWSER="default"

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  --skip-cleanup    Saltar limpieza de instalación anterior"
    echo "  --skip-build      Saltar construcción de imágenes Docker"
    echo "  --skip-tests      Saltar ejecución de pruebas"
    echo "  --browser BROWSER Especificar navegador (chrome, firefox, default)"
    echo "  -h, --help        Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0                           # Despliegue completo"
    echo "  $0 --skip-cleanup           # Saltar limpieza"
    echo "  $0 --browser chrome         # Usar Chrome"
}

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-cleanup)
            SKIP_CLEANUP=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --browser)
            BROWSER="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Funciones de utilidad
print_color() {
    local color=$1
    local message=$2
    local prefix=$3
    local timestamp=$(date +"%H:%M:%S")
    echo -e "${color}[$timestamp] $prefix$message${NC}"
}

print_header() {
    local title=$1
    echo ""
    echo -e "${MAGENTA}============================================================${NC}"
    echo -e "${MAGENTA}  $title${NC}"
    echo -e "${MAGENTA}============================================================${NC}"
    echo ""
}

print_step() {
    local step=$1
    local total=$2
    local message=$3
    print_color $CYAN "Paso $step/$total - $message" "🔧 "
}

test_command() {
    local cmd=$1
    if command -v "$cmd" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

wait_for_service() {
    local url=$1
    local service_name=$2
    local max_wait=${3:-60}
    
    print_color $CYAN "Esperando que $service_name esté disponible..." "⏳ "
    
    local elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_color $GREEN "$service_name está disponible" "✅ "
            return 0
        fi
        
        sleep 2
        elapsed=$((elapsed + 2))
        printf "\r⏳ Esperando $service_name... %d/%d segundos" $elapsed $max_wait
    done
    
    echo ""
    print_color $RED "$service_name no está disponible después de $max_wait segundos" "❌ "
    return 1
}

open_browser() {
    local url=$1
    
    print_color $CYAN "Abriendo interfaz web en el navegador..." "🌐 "
    
    case $BROWSER in
        "chrome")
            google-chrome "$url" 2>/dev/null || chromium-browser "$url" 2>/dev/null || print_color $YELLOW "Chrome no encontrado" "⚠️ "
            ;;
        "firefox")
            firefox "$url" 2>/dev/null || print_color $YELLOW "Firefox no encontrado" "⚠️ "
            ;;
        "default"|*)
            if command -v xdg-open &> /dev/null; then
                xdg-open "$url" 2>/dev/null
            elif command -v open &> /dev/null; then
                open "$url" 2>/dev/null
            else
                print_color $YELLOW "No se pudo abrir el navegador automáticamente" "⚠️ "
                print_color $CYAN "Abra manualmente: $url" "💡 "
                return
            fi
            ;;
    esac
    
    print_color $GREEN "Navegador abierto en $url" "✅ "
}

# Inicio del script
print_header "🚀 DESPLIEGUE COMPLETO DE $PROJECT_NAME"

# Verificar prerrequisitos
print_step 1 9 "Verificando prerrequisitos..."

if test_command "docker"; then
    print_color $GREEN "Docker está instalado" "✅ "
else
    print_color $RED "Docker NO está instalado" "❌ "
    exit 1
fi

if test_command "docker-compose"; then
    print_color $GREEN "Docker Compose está instalado" "✅ "
else
    print_color $RED "Docker Compose NO está instalado" "❌ "
    exit 1
fi

# Limpiar instalación anterior
if [ "$SKIP_CLEANUP" = false ]; then
    print_step 2 9 "Limpiando instalación anterior..."
    
    print_color $CYAN "Deteniendo contenedores existentes..." "🛑 "
    docker-compose down --remove-orphans 2>/dev/null
    
    print_color $CYAN "Eliminando contenedores huérfanos..." "🗑️ "
    docker container prune -f 2>/dev/null
    
    print_color $CYAN "Eliminando imágenes no utilizadas..." "🗑️ "
    docker image prune -f 2>/dev/null
    
    print_color $GREEN "Limpieza completada" "✅ "
else
    print_color $YELLOW "Saltando limpieza (--skip-cleanup especificado)" "⚠️ "
fi

# Crear red Docker
print_step 3 9 "Configurando red Docker..."

if docker network ls --format "{{.Name}}" | grep -q "^$NETWORK_NAME$"; then
    print_color $CYAN "Red '$NETWORK_NAME' ya existe" "ℹ️ "
else
    print_color $CYAN "Creando red '$NETWORK_NAME'..." "🌐 "
    if docker network create "$NETWORK_NAME" 2>/dev/null; then
        print_color $GREEN "Red '$NETWORK_NAME' creada" "✅ "
    else
        print_color $RED "Error creando red '$NETWORK_NAME'" "❌ "
        exit 1
    fi
fi

# Crear directorios necesarios
print_step 4 9 "Creando estructura de directorios..."

directories=(
    "data/central-server"
    "data/shared-files/peer1"
    "data/shared-files/peer2"
    "data/shared-files/peer3"
    "config"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_color $GREEN "Directorio '$dir' creado" "📁 "
    else
        print_color $CYAN "Directorio '$dir' ya existe" "ℹ️ "
    fi
done

# Construir imágenes
if [ "$SKIP_BUILD" = false ]; then
    print_step 5 9 "Construyendo imágenes Docker..."
    
    print_color $CYAN "Construyendo imagen del servidor central..." "🔨 "
    if ! docker-compose build central-server; then
        print_color $RED "Error construyendo servidor central" "❌ "
        exit 1
    fi
    
    print_color $CYAN "Construyendo imagen de nodos peer..." "🔨 "
    if ! docker-compose build peer-node-1 peer-node-2 peer-node-3; then
        print_color $RED "Error construyendo nodos peer" "❌ "
        exit 1
    fi
    
    print_color $GREEN "Imágenes construidas correctamente" "✅ "
else
    print_color $YELLOW "Saltando construcción (--skip-build especificado)" "⚠️ "
fi

# Recrear base de datos
print_step 6 9 "Recreando base de datos..."

# Ejecutar dentro del contenedor para usar dependencias (SQLAlchemy)
DB_URL="sqlite:////app/data/central_server.db"
print_color $CYAN "Ejecutando creación de tablas dentro del contenedor..." "🗄️ "
if ! docker-compose run --rm -e DATABASE_URL="$DB_URL" central-server python /app/init_db.py; then
    print_color $RED "Error recreando base de datos (docker-compose run)" "❌ "
    exit 1
fi
print_color $GREEN "Base de datos recreada correctamente" "✅ "

# Iniciar servicios
print_step 7 9 "Iniciando servicios..."

print_color $CYAN "Iniciando servidor central..." "🚀 "
if ! docker-compose up -d central-server; then
    print_color $RED "Error iniciando servidor central" "❌ "
    exit 1
fi

# Esperar a que el servidor central esté disponible
if ! wait_for_service "$CENTRAL_SERVER_URL/api/health" "Servidor Central" $TIMEOUT; then
    print_color $RED "El servidor central no está respondiendo" "❌ "
    print_color $CYAN "Revisando logs del servidor central..." "📋 "
    docker logs p2p-central-server --tail 20
    exit 1
fi

print_color $CYAN "Iniciando nodos peer..." "🚀 "
if ! docker-compose up -d peer-node-1 peer-node-2 peer-node-3; then
    print_color $RED "Error iniciando nodos peer" "❌ "
    exit 1
fi

# Esperar a que los peers se registren
print_color $CYAN "Esperando que los peers se registren..." "⏳ "
sleep 10

# Verificar estado de los servicios
print_step 8 9 "Verificando estado de los servicios..."

services=(
    "p2p-central-server:8000:Servidor Central"
    "p2p-peer-1:8001:Peer 1"
    "p2p-peer-2:8002:Peer 2"
    "p2p-peer-3:8003:Peer 3"
)

all_services_running=true
for service in "${services[@]}"; do
    IFS=':' read -r container port name <<< "$service"
    container_status=$(docker inspect "$container" --format "{{.State.Status}}" 2>/dev/null)
    
    if [ "$container_status" = "running" ]; then
        print_color $GREEN "$name está ejecutándose" "✅ "
    else
        print_color $RED "$name NO está ejecutándose (Estado: $container_status)" "❌ "
        all_services_running=false
    fi
done

if [ "$all_services_running" = false ]; then
    print_color $RED "Algunos servicios no están ejecutándose correctamente" "❌ "
    print_color $CYAN "Revisando logs..." "📋 "
    docker-compose logs --tail 10
    exit 1
fi

# Ejecutar pruebas
if [ "$SKIP_TESTS" = false ]; then
    print_step 9 9 "Ejecutando pruebas del sistema..."
    
    test_script="scripts/test_web_interface.py"
    if [ -f "$test_script" ]; then
        print_color $CYAN "Ejecutando pruebas de la interfaz web..." "🧪 "
        if python3 "$test_script" --url "$CENTRAL_SERVER_URL" --timeout 30; then
            print_color $GREEN "Pruebas completadas exitosamente" "✅ "
        else
            print_color $YELLOW "Algunas pruebas fallaron" "⚠️ "
        fi
    else
        print_color $YELLOW "Script de pruebas no encontrado, saltando..." "⚠️ "
    fi
else
    print_color $YELLOW "Saltando pruebas (--skip-tests especificado)" "⚠️ "
fi

# Mostrar información del sistema
print_header "📊 INFORMACIÓN DEL SISTEMA"

print_color $CYAN "Servicios desplegados:" "ℹ️ "
print_color $GREEN "  • Servidor Central: $CENTRAL_SERVER_URL" "🌐 "
print_color $GREEN "  • Peer 1: http://localhost:8001" "🌐 "
print_color $GREEN "  • Peer 2: http://localhost:8002" "🌐 "
print_color $GREEN "  • Peer 3: http://localhost:8003" "🌐 "

print_color $CYAN "Comandos útiles:" "ℹ️ "
print_color $CYAN "  • Ver logs: docker-compose logs -f" "📋 "
print_color $CYAN "  • Detener: docker-compose down" "🛑 "
print_color $CYAN "  • Reiniciar: docker-compose restart" "🔄 "
print_color $CYAN "  • Estado: docker-compose ps" "📊 "

# Abrir interfaz web
print_header "🌐 ABRIENDO INTERFAZ WEB"

open_browser "$CENTRAL_SERVER_URL"

# Esperar un momento para que el navegador se abra
sleep 2

print_header "🎉 DESPLIEGUE COMPLETADO"

print_color $GREEN "¡RedP2P ha sido desplegado exitosamente!" "🎉 "
print_color $GREEN "La interfaz web debería abrirse automáticamente en tu navegador" "🌐 "
print_color $CYAN "Si no se abre, visita manualmente: $CENTRAL_SERVER_URL" "💡 "

print_color $CYAN "Para detener el sistema, ejecuta:" "ℹ️ "
print_color $YELLOW "  docker-compose down" "⚠️ "

print_color $GREEN "¡Disfruta usando RedP2P! 🚀" "✨ "

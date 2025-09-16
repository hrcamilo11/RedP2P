# Red P2P - Sistema de Compartir Archivos

Sistema distribuido de compartir archivos peer-to-peer con servidor central de coordinación.

## 📁 Estructura del Proyecto

```
RedP2P/
├── src/                          # Código fuente
│   ├── central-server/           # Servidor central
│   │   ├── api/                  # API REST
│   │   ├── models/               # Modelos de datos
│   │   ├── services/             # Servicios del servidor
│   │   ├── static/               # Interfaz web
│   │   └── init_db.py            # Inicialización de base de datos
│   └── peer-node/                # Nodo peer
│       ├── api/                  # API REST y gRPC
│       ├── models/               # Modelos de datos
│       └── requirements.txt      # Dependencias del peer
├── config/                       # Configuraciones
│   ├── peer1.json                # Configuración peer 1
│   ├── peer2.json                # Configuración peer 2
│   └── peer3.json                # Configuración peer 3
├── data/                         # Datos persistentes
│   ├── central-server/           # Base de datos del servidor (host)
│   │   ├── central_server.db     # Archivo SQLite
│   │   └── central_server.db.backup
│   └── shared-files/             # Archivos compartidos
│       ├── peer1/
│       ├── peer2/
│       └── peer3/
├── scripts/                      # Scripts de automatización
│   ├── recreate_database.py      # Recreación de la base de datos (host)
│   └── ...
├── docker-compose.yml            # Orquestación de contenedores
├── deploy.ps1 / deploy.sh        # Despliegue automático
├── QUICK_START.md                # Guía rápida
├── DEPLOY.md                     # Guía de despliegue
└── README.md                     # Este archivo
```

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose
- PowerShell (Windows) o Bash (Linux/macOS)

### Despliegue Automático (Recomendado)

#### Windows
```powershell
# Despliegue completo con interfaz web
.\deploy.ps1

# Con opciones personalizadas
.\deploy.ps1 -SkipCleanup -Browser chrome
```

#### Linux/macOS
```bash
# Despliegue completo con interfaz web
./deploy.sh

# Con opciones personalizadas
./deploy.sh --skip-cleanup --browser chrome
```

### Despliegue Manual

#### 1. Configurar red Docker
```powershell
docker network create p2p-network
```

#### 2. Iniciar el sistema
```powershell
docker-compose up -d --build
```

#### 3. Acceder a la interfaz
Abrir http://localhost:8000 en el navegador

Nota: Durante el despliegue se recrea la base de datos del servidor central antes de levantar los servicios. La base de datos de host queda en `data/central-server/central_server.db` (mapeada al contenedor como `/app/data/central_server.db`).

### 🎯 Interfaz Web Incluye
- **Dashboard**: Estadísticas en tiempo real del sistema
- **Gestión de Peers**: Visualización y control de peers conectados
- **Archivos**: Búsqueda, subida y descarga de archivos
- **Transferencias**: Monitoreo de transferencias activas

## 🏗️ Arquitectura

### Servidor Central
- **Coordinación**: Gestiona la red de peers
- **Índice Central**: Mantiene catálogo de archivos
- **API REST**: Interfaz de comunicación
- **Interfaz Web**: Centro de control

### Nodos Peer
- **Almacenamiento**: Archivos compartidos
- **API REST**: Comunicación con servidor central
- **gRPC**: Comunicación entre peers
- **Servicios**: Indexación, localización, transferencia

## 🔧 Funcionalidades

### Centro de Control
- **Dashboard interactivo** con estadísticas en tiempo real
- **Gestión visual de peers** con estado de conexión
- **Búsqueda avanzada de archivos** con filtros múltiples
- **Subida y descarga** de archivos con interfaz drag & drop
- **Monitoreo de transferencias** con barras de progreso
- **Interfaz responsiva** para desktop, tablet y móvil

### Red P2P
- Compartir archivos entre peers
- Descarga directa desde peers
- Indexación automática
- Transferencias en tiempo real

## 📊 API Endpoints

### Servidor Central
- `GET /api/stats` - Estadísticas del sistema
- `GET /api/peers` - Lista de peers
- `GET /api/files/peer/{peer_id}` - Archivos de un peer
- `POST /api/files/search` - Búsqueda de archivos

### Nodos Peer
- `GET /api/files` - Archivos del peer
- `GET /api/download/{file_hash}` - Descargar archivo
- `POST /api/upload` - Subir archivo

## 🛠️ Desarrollo

### Estructura de Servicios
- **PeerManager**: Gestión de peers
- **FileIndexer**: Indexación de archivos
- **TransferManager**: Gestión de transferencias
- **CentralClient**: Cliente del servidor central

### Tecnologías
- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript ES6+, Bootstrap 5
- **Interfaz Web**: Diseño responsivo, Bootstrap Icons, Fetch API
- **Comunicación**: REST API, gRPC
- **Contenedores**: Docker, Docker Compose
- **Base de Datos**: SQLite

## 📝 Scripts Disponibles

### Despliegue
- `deploy.ps1` / `deploy.sh` - **Despliegue completo automático** (Recomendado)
- `scripts/start.ps1` - Iniciar sistema manualmente
- `scripts/stop.ps1` - Detener sistema
- `scripts/cleanup.ps1` - Limpiar contenedores

### Pruebas
- `scripts/test_web_interface.ps1` - Probar interfaz web (PowerShell)
- `scripts/test_web_interface.py` - Pruebas automatizadas Python

Sugerencia Windows: si ves errores de Unicode en consola, ejecuta previamente:
```powershell
chcp 65001
$env:PYTHONIOENCODING = "utf-8"
```

## 🔍 Monitoreo

### Logs
```powershell
# Ver logs del servidor central
docker logs p2p-central-server

# Ver logs de un peer
docker logs p2p-peer-1
```

### Estado del Sistema
```powershell
# Verificar contenedores
docker ps

# Verificar red
docker network ls
```

## 🐛 Solución de Problemas

### Problemas Comunes
1. **Red no existe**: Ejecutar `docker network create p2p-network`
2. **Puertos ocupados**: Verificar que los puertos 8000-8003 estén libres
3. **Archivos no aparecen**: Verificar que los peers estén online

### Reiniciar Sistema
```powershell
docker-compose down
docker-compose up -d --build
```

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.
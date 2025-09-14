# Arquitectura de la Interfaz Web RedP2P

## 📐 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTERFAZ WEB REDP2P                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   NAVEGACIÓN    │    │   DASHBOARD     │    │   PEERS      │ │
│  │                 │    │                 │    │              │ │
│  │ • Dashboard     │    │ • Stats Cards   │    │ • Lista      │ │
│  │ • Peers         │    │ • Acciones      │    │ • Filtros    │ │
│  │ • Archivos      │    │ • Actividad     │    │ • Acciones   │ │
│  │ • Transferencias│    │   Reciente      │    │ • Estado     │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   ARCHIVOS      │    │ TRANSFERENCIAS  │                    │
│  │                 │    │                 │                    │
│  │ • Búsqueda      │    │ • Activas       │                    │
│  │ • Subida        │    │ • Historial     │                    │
│  │ • Descarga      │    │ • Progreso      │                    │
│  │ • Lista         │    │ • Estados       │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │    HTML5    │  │    CSS3     │  │ JavaScript  │            │
│  │             │  │             │  │             │            │
│  │ • Semántico │  │ • Bootstrap │  │ • ES6+      │            │
│  │ • Accesible │  │ • Responsivo│  │ • Fetch API │            │
│  │ • Estructura│  │ • Animaciones│  │ • Clases    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE COMUNICACIÓN                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    REST API                                │ │
│  │                                                             │ │
│  │  GET  /api/stats          - Estadísticas del sistema       │ │
│  │  GET  /api/peers          - Lista de peers                 │ │
│  │  GET  /api/peers/online   - Peers online                   │ │
│  │  POST /api/files/search   - Búsqueda de archivos           │ │
│  │  GET  /api/files/peer/{id} - Archivos de un peer           │ │
│  │  POST /api/transfers/download - Iniciar descarga           │ │
│  │  POST /api/transfers/upload   - Iniciar subida             │ │
│  │  GET  /api/transfers/active   - Transferencias activas     │ │
│  │  GET  /api/transfers/history  - Historial                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVIDOR CENTRAL                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   FastAPI   │  │ SQLAlchemy  │  │   Servicios │            │
│  │             │  │             │  │             │            │
│  │ • REST API  │  │ • Base de   │  │ • PeerMgr   │            │
│  │ • CORS      │  │   Datos     │  │ • FileIdx   │            │
│  │ • Static    │  │ • Modelos   │  │ • TransferMgr│           │
│  │ • Docs      │  │ • Migraciones│  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Flujo de Datos

### 1. Carga Inicial
```
Usuario → Navegador → HTML/CSS/JS → API → Base de Datos
```

### 2. Navegación
```
Click → JavaScript → showSection() → Actualizar DOM → Cargar datos
```

### 3. Búsqueda de Archivos
```
Formulario → JavaScript → POST /api/files/search → Base de Datos → Resultados
```

### 4. Gestión de Peers
```
Acción → JavaScript → API → Servicios → Base de Datos → Actualizar UI
```

### 5. Transferencias
```
Descarga → JavaScript → API → TransferManager → Peer → Archivo
```

## 🏗️ Componentes Principales

### Frontend (Cliente)
- **HTML5**: Estructura semántica y accesible
- **CSS3**: Estilos modernos con Bootstrap 5
- **JavaScript ES6+**: Lógica de aplicación con clases
- **Bootstrap Icons**: Iconografía consistente

### Backend (Servidor)
- **FastAPI**: Framework web asíncrono
- **SQLAlchemy**: ORM para base de datos
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI

### Base de Datos
- **SQLite**: Base de datos ligera
- **Modelos**: Peer, File, TransferLog, SearchLog
- **Relaciones**: Peer ↔ Files (1:N)

## 📱 Responsive Design

### Breakpoints
- **Desktop**: > 1200px - Experiencia completa
- **Tablet**: 768px - 1199px - Layout adaptado
- **Mobile**: < 768px - Interfaz táctil

### Adaptaciones
- **Navegación**: Collapse en móvil
- **Cards**: Stack vertical en móvil
- **Botones**: Tamaño táctil en móvil
- **Tablas**: Scroll horizontal en móvil

## 🔧 Configuración

### Variables de Entorno
```bash
DATABASE_URL=sqlite:///./central_server.db
HOST=0.0.0.0
PORT=8000
```

### Configuración de CORS
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🚀 Despliegue

### Desarrollo
```bash
# Servidor central
cd src/central-server
python main.py

# Interfaz web
# Acceder a http://localhost:8000
```

### Producción
```bash
# Con Docker
docker-compose up -d

# Interfaz disponible en http://localhost:8000
```

## 🔍 Monitoreo

### Métricas Disponibles
- **Peers**: Total, online, offline
- **Archivos**: Total, tamaño, por peer
- **Transferencias**: Activas, completadas, fallidas
- **Rendimiento**: Tiempo de respuesta, uso de memoria

### Logs
- **Acceso**: Requests HTTP
- **Errores**: Excepciones y fallos
- **Transferencias**: Progreso y estados
- **Base de datos**: Queries y transacciones

## 🛠️ Mantenimiento

### Tareas Regulares
- **Limpieza**: Peers offline antiguos
- **Indexación**: Archivos de peers
- **Logs**: Rotación de archivos de log
- **Backup**: Base de datos

### Actualizaciones
- **Frontend**: Cache busting con versiones
- **Backend**: Migraciones de base de datos
- **Dependencias**: Actualización de paquetes
- **Seguridad**: Parches de seguridad

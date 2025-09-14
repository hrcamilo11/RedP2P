# RedP2P - Interfaz Web del Servidor Central

## 📋 Descripción

Interfaz web moderna y responsiva para el servidor central de RedP2P que permite gestionar peers, archivos y transferencias de forma intuitiva.

## 🎨 Características

### Dashboard Principal
- **Estadísticas en tiempo real**: Total de peers, peers online, archivos y tamaño total
- **Acciones rápidas**: Botones para actualizar stats, indexar archivos y navegar
- **Actividad reciente**: Historial de las últimas transferencias

### Gestión de Peers
- **Lista completa de peers**: Visualización de todos los peers registrados
- **Filtros inteligentes**: Ver todos, solo online o solo offline
- **Acciones por peer**:
  - Indexar archivos del peer
  - Ver archivos del peer
  - Conectar/desconectar peer
- **Estado en tiempo real**: Indicadores visuales de conexión

### Gestión de Archivos
- **Búsqueda avanzada**: Por nombre, tamaño, peer específico
- **Subida de archivos**: Interfaz drag & drop con selección de peer destino
- **Visualización detallada**: Lista con información completa de archivos
- **Descarga directa**: Botones de descarga con confirmación

### Monitoreo de Transferencias
- **Transferencias activas**: Progreso en tiempo real con barras de progreso
- **Historial completo**: Todas las transferencias realizadas
- **Estados detallados**: Pending, initiated, completed, failed
- **Filtros por tipo**: Activas o todas las transferencias

## 🛠️ Tecnologías Utilizadas

- **HTML5**: Estructura semántica y accesible
- **CSS3**: Estilos modernos con Flexbox y Grid
- **Bootstrap 5**: Framework CSS responsivo
- **JavaScript ES6+**: Lógica de aplicación moderna
- **Bootstrap Icons**: Iconografía consistente
- **Fetch API**: Comunicación con la API REST

## 📱 Diseño Responsivo

La interfaz está completamente optimizada para:
- **Desktop**: Experiencia completa con todas las funcionalidades
- **Tablet**: Layout adaptado con navegación optimizada
- **Mobile**: Interfaz táctil con botones y elementos redimensionados

## 🎯 Funcionalidades Principales

### 1. Navegación Intuitiva
- Barra de navegación con indicadores de sección activa
- Navegación por pestañas con transiciones suaves
- Estado de conexión en tiempo real

### 2. Dashboard Interactivo
- Cards de estadísticas con animaciones
- Actualización automática cada 30 segundos
- Acciones rápidas para tareas comunes

### 3. Gestión de Peers
- Lista visual con estado de conexión
- Filtros dinámicos por estado
- Acciones contextuales por peer

### 4. Búsqueda de Archivos
- Formulario de búsqueda con múltiples criterios
- Resultados paginados y filtrados
- Información detallada de cada archivo

### 5. Transferencias
- Monitoreo en tiempo real del progreso
- Historial completo de transferencias
- Estados visuales claros

## 🔧 Configuración

### Variables de Entorno
```javascript
// En app.js
this.apiBaseUrl = '/api';  // URL base de la API
```

### Personalización
- **Colores**: Modificar variables CSS en `styles.css`
- **Intervalos**: Cambiar tiempo de actualización automática
- **Funcionalidades**: Extender la clase `RedP2PApp` en `app.js`

## 📊 API Endpoints Utilizados

### Dashboard
- `GET /api/stats` - Estadísticas del sistema
- `GET /api/transfers/history?limit=5` - Actividad reciente

### Peers
- `GET /api/peers` - Lista de todos los peers
- `POST /api/files/index/{peer_id}` - Indexar archivos de un peer

### Archivos
- `POST /api/files/search` - Buscar archivos
- `GET /api/files/peer/{peer_id}` - Archivos de un peer específico
- `GET /api/files/{file_hash}` - Información de un archivo

### Transferencias
- `GET /api/transfers/active` - Transferencias activas
- `GET /api/transfers/history` - Historial de transferencias
- `POST /api/transfers/download` - Iniciar descarga
- `POST /api/transfers/upload` - Iniciar subida

## 🎨 Personalización Visual

### Colores Principales
```css
:root {
    --primary-color: #0d6efd;
    --success-color: #198754;
    --info-color: #0dcaf0;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
}
```

### Animaciones
- Transiciones suaves en hover
- Animaciones de carga
- Efectos de pulso para indicadores de estado

## 🔍 Solución de Problemas

### Problemas Comunes

1. **No se cargan los datos**
   - Verificar que el servidor central esté ejecutándose
   - Comprobar la consola del navegador para errores

2. **Errores de CORS**
   - El servidor central debe tener CORS habilitado
   - Verificar configuración en `rest_api.py`

3. **Archivos no se suben**
   - Verificar que el peer destino esté online
   - Comprobar permisos de archivos

### Debug
- Abrir herramientas de desarrollador (F12)
- Revisar pestaña Network para errores de API
- Verificar consola para errores JavaScript

## 🚀 Mejoras Futuras

- [ ] Notificaciones push en tiempo real
- [ ] Gráficos de estadísticas con Chart.js
- [ ] Modo oscuro
- [ ] Exportación de datos
- [ ] Configuración avanzada de peers
- [ ] Logs en tiempo real
- [ ] Métricas de rendimiento

## 📝 Notas de Desarrollo

- La interfaz está diseñada para ser modular y extensible
- Todas las llamadas a la API incluyen manejo de errores
- El código está optimizado para rendimiento y accesibilidad
- Compatible con navegadores modernos (ES6+)

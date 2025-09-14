# 🚀 Guía de Inicio Rápido - RedP2P

## ⚡ Despliegue en 1 Minuto

### Windows
```powershell
# 1. Clonar el repositorio
git clone <repository-url>
cd RedP2P

# 2. Desplegar automáticamente
.\deploy.ps1

# 3. ¡Listo! La interfaz se abre automáticamente
```

### Linux/macOS
```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd RedP2P

# 2. Desplegar automáticamente
./deploy.sh

# 3. ¡Listo! La interfaz se abre automáticamente
```

## 🎯 Primeros Pasos

### 1. Explorar el Dashboard
- **Estadísticas**: Ver total de peers, archivos y tamaño
- **Acciones rápidas**: Indexar archivos, actualizar stats
- **Actividad reciente**: Historial de transferencias

### 2. Gestionar Peers
- **Ver peers conectados**: Lista con estado de conexión
- **Filtrar por estado**: Online, offline, todos
- **Acciones por peer**: Indexar archivos, ver archivos, conectar/desconectar

### 3. Buscar Archivos
- **Búsqueda simple**: Por nombre de archivo
- **Filtros avanzados**: Por tamaño, peer específico
- **Resultados detallados**: Información completa de cada archivo

### 4. Subir Archivos
- **Seleccionar archivos**: Drag & drop o botón de selección
- **Elegir peer destino**: Lista desplegable de peers disponibles
- **Confirmar subida**: Proceso automático de indexación

### 5. Descargar Archivos
- **Buscar archivo**: Usar la búsqueda avanzada
- **Hacer clic en "Descargar"**: Confirmar en el modal
- **Descarga automática**: El archivo se descarga directamente

## 🔧 Comandos Útiles

### Ver Estado del Sistema
```bash
# Estado de contenedores
docker-compose ps

# Logs en tiempo real
docker-compose logs -f

# Estadísticas de recursos
docker stats
```

### Gestionar Servicios
```bash
# Reiniciar todo
docker-compose restart

# Reiniciar solo el servidor central
docker-compose restart central-server

# Detener todo
docker-compose down

# Detener y limpiar
docker-compose down --remove-orphans
```

### Pruebas Rápidas
```bash
# Probar API del servidor central
curl http://localhost:8000/api/health

# Ver estadísticas
curl http://localhost:8000/api/stats

# Listar peers
curl http://localhost:8000/api/peers
```

## 📱 Interfaz Web - Guía de Usuario

### Dashboard Principal
- **Cards de estadísticas**: Información en tiempo real
- **Botón "Actualizar Stats"**: Refrescar datos
- **Botón "Indexar Archivos"**: Actualizar índice de archivos
- **Actividad reciente**: Últimas transferencias

### Sección de Peers
- **Lista de peers**: Todos los peers registrados
- **Filtros**: Botones para filtrar por estado
- **Acciones por peer**:
  - 🔍 **Indexar**: Actualizar archivos del peer
  - 📁 **Ver Archivos**: Mostrar archivos del peer
  - 🔌 **Conectar/Desconectar**: Cambiar estado del peer

### Sección de Archivos
- **Formulario de búsqueda**:
  - Nombre del archivo
  - Tamaño mínimo/máximo (en MB)
  - Peer específico
- **Subida de archivos**:
  - Seleccionar archivos
  - Elegir peer destino
  - Botón "Subir"
- **Lista de resultados**:
  - Información detallada
  - Botón "Descargar"
  - Botón "Info"

### Sección de Transferencias
- **Filtros**: Activas o todas las transferencias
- **Lista de transferencias**:
  - Progreso visual con barras
  - Estado actual
  - Información de archivo y peers
  - Tiempo de inicio

## 🎮 Casos de Uso Comunes

### Caso 1: Compartir un Archivo
1. **Subir archivo**:
   - Ir a sección "Archivos"
   - Hacer clic en "Seleccionar archivo"
   - Elegir peer destino
   - Hacer clic en "Subir"

2. **Verificar subida**:
   - El archivo aparece en la lista
   - Estado "disponible" en el peer

### Caso 2: Buscar y Descargar
1. **Buscar archivo**:
   - Ir a sección "Archivos"
   - Escribir nombre en búsqueda
   - Hacer clic en "Buscar"

2. **Descargar archivo**:
   - Hacer clic en "Descargar"
   - Confirmar en el modal
   - El archivo se descarga automáticamente

### Caso 3: Monitorear Transferencias
1. **Ver transferencias activas**:
   - Ir a sección "Transferencias"
   - Filtrar por "Activas"
   - Ver progreso en tiempo real

2. **Ver historial**:
   - Cambiar filtro a "Todas"
   - Revisar transferencias completadas

### Caso 4: Gestionar Peers
1. **Ver estado de peers**:
   - Ir a sección "Peers"
   - Ver lista con indicadores de estado
   - Usar filtros para ver solo online/offline

2. **Indexar archivos de un peer**:
   - Hacer clic en "Indexar" en el peer deseado
   - Ver confirmación de indexación
   - Los archivos aparecen en la búsqueda

## 🔍 Solución de Problemas Rápidos

### La interfaz no carga
```bash
# Verificar que el servidor esté ejecutándose
docker-compose ps

# Ver logs del servidor central
docker logs p2p-central-server

# Reiniciar si es necesario
docker-compose restart central-server
```

### No aparecen archivos
```bash
# Indexar archivos de todos los peers
# En la interfaz: Dashboard → "Indexar Archivos"

# O manualmente por API
curl -X POST http://localhost:8000/api/files/index-all
```

### Los peers no se conectan
```bash
# Verificar logs de peers
docker logs p2p-peer-1
docker logs p2p-peer-2
docker logs p2p-peer-3

# Reiniciar peers
docker-compose restart peer-node-1 peer-node-2 peer-node-3
```

### Error de permisos
```bash
# En Linux/macOS, agregar usuario al grupo docker
sudo usermod -aG docker $USER
# Reiniciar sesión
```

## 📊 Monitoreo del Sistema

### Métricas Importantes
- **Peers online**: Debería ser 3
- **Archivos totales**: Depende de archivos en shared-files/
- **Transferencias activas**: 0 en reposo
- **Tamaño total**: Suma de todos los archivos

### Alertas a Revisar
- ⚠️ **Peer offline**: Verificar logs del peer
- ⚠️ **Sin archivos**: Ejecutar indexación
- ⚠️ **Transferencia fallida**: Revisar conectividad
- ⚠️ **Alto uso de CPU**: Verificar recursos del sistema

## 🎉 ¡Disfruta Usando RedP2P!

Con esta guía deberías poder:
- ✅ **Desplegar** el sistema en menos de 1 minuto
- ✅ **Navegar** por la interfaz web intuitiva
- ✅ **Compartir** archivos entre peers
- ✅ **Buscar y descargar** archivos fácilmente
- ✅ **Monitorear** el estado del sistema
- ✅ **Solucionar** problemas comunes

### Próximos Pasos
- 📖 Leer la documentación completa en `README.md`
- 🔧 Personalizar la configuración en `config/`
- 🧪 Ejecutar pruebas con `scripts/test_web_interface.ps1`
- 🚀 Explorar funcionalidades avanzadas

¡Bienvenido a RedP2P! 🚀

# 🚀 Guía de Despliegue - RedP2P

## Descripción

Scripts de despliegue automatizado que realizan una instalación limpia de todos los servicios de RedP2P y abren la interfaz web automáticamente.

## 📋 Prerrequisitos

### Windows
- **PowerShell 5.1+** o **PowerShell Core 7+**
- **Docker Desktop** para Windows
- **Docker Compose** (incluido con Docker Desktop)

### Linux/macOS
- **Bash 4.0+**
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Python 3.7+** (para pruebas)

## 🚀 Uso Rápido

### Windows
```powershell
# Despliegue completo
.\deploy.ps1

# Con opciones
.\deploy.ps1 -SkipCleanup -Browser chrome
```

### Linux/macOS
```bash
# Despliegue completo
./deploy.sh

# Con opciones
./deploy.sh --skip-cleanup --browser chrome
```

## ⚙️ Opciones Disponibles

### Windows (PowerShell)
| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `-SkipCleanup` | Saltar limpieza de instalación anterior | `false` |
| `-SkipBuild` | Saltar construcción de imágenes Docker | `false` |
| `-SkipTests` | Saltar ejecución de pruebas | `false` |
| `-Browser` | Navegador a usar | `"default"` |

### Linux/macOS (Bash)
| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--skip-cleanup` | Saltar limpieza de instalación anterior | `false` |
| `--skip-build` | Saltar construcción de imágenes Docker | `false` |
| `--skip-tests` | Saltar ejecución de pruebas | `false` |
| `--browser` | Navegador a usar | `"default"` |

### Navegadores Soportados
- `default` - Navegador por defecto del sistema
- `chrome` - Google Chrome
- `firefox` - Mozilla Firefox
- `edge` - Microsoft Edge (solo Windows)

## 📋 Proceso de Despliegue

El script realiza los siguientes pasos:

### 1. Verificación de Prerrequisitos
- ✅ Docker instalado y funcionando
- ✅ Docker Compose disponible
- ✅ Permisos necesarios

### 2. Limpieza (opcional)
- 🛑 Detener contenedores existentes
- 🗑️ Eliminar contenedores huérfanos
- 🗑️ Limpiar imágenes no utilizadas

### 3. Configuración de Red
- 🌐 Crear red Docker `p2p-network`
- 📁 Crear estructura de directorios

### 4. Construcción de Imágenes
- 🔨 Construir imagen del servidor central
- 🔨 Construir imágenes de nodos peer

### 5. Inicio de Servicios
- 🚀 Iniciar servidor central
- ⏳ Esperar disponibilidad del servidor
- 🚀 Iniciar nodos peer
- ⏳ Esperar registro de peers

### 6. Verificación
- ✅ Verificar estado de todos los servicios
- 🧪 Ejecutar pruebas automatizadas
- 📊 Mostrar información del sistema

### 7. Apertura de Interfaz
- 🌐 Abrir navegador automáticamente
- 📱 Mostrar URLs de acceso

## 🎯 Servicios Desplegados

| Servicio | Puerto | URL | Descripción |
|----------|--------|-----|-------------|
| Servidor Central | 8000 | http://localhost:8000 | Interfaz web y API |
| Peer 1 | 8001 | http://localhost:8001 | Nodo peer 1 |
| Peer 2 | 8002 | http://localhost:8002 | Nodo peer 2 |
| Peer 3 | 8003 | http://localhost:8003 | Nodo peer 3 |

## 🔧 Comandos Útiles

### Gestión de Servicios
```bash
# Ver estado de servicios
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f central-server

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down
```

### Limpieza
```bash
# Detener y eliminar contenedores
docker-compose down --remove-orphans

# Eliminar volúmenes
docker-compose down -v

# Limpiar sistema Docker
docker system prune -a
```

## 🐛 Solución de Problemas

### Error: "Docker no está instalado"
**Solución**: Instalar Docker Desktop desde [docker.com](https://www.docker.com/products/docker-desktop)

### Error: "Red p2p-network ya existe"
**Solución**: Normal, el script maneja esto automáticamente

### Error: "Servidor central no responde"
**Solución**: 
1. Verificar logs: `docker logs p2p-central-server`
2. Verificar puerto 8000 libre: `netstat -an | findstr :8000`
3. Reiniciar Docker Desktop

### Error: "Peers no se registran"
**Solución**:
1. Verificar que el servidor central esté funcionando
2. Verificar logs de peers: `docker logs p2p-peer-1`
3. Verificar configuración en `config/peer*.json`

### Error: "Navegador no se abre"
**Solución**:
1. Abrir manualmente: http://localhost:8000
2. Verificar que el puerto 8000 esté accesible
3. Verificar firewall/antivirus

## 📊 Monitoreo

### Verificar Estado
```bash
# Estado de contenedores
docker-compose ps

# Uso de recursos
docker stats

# Logs del sistema
docker-compose logs --tail 50
```

### Pruebas de Conectividad
```bash
# Servidor central
curl http://localhost:8000/api/health

# Peer 1
curl http://localhost:8001/api/health

# API de estadísticas
curl http://localhost:8000/api/stats
```

## 🔄 Actualizaciones

### Actualizar Código
```bash
# Detener servicios
docker-compose down

# Actualizar código (git pull, etc.)

# Reconstruir y desplegar
./deploy.sh --skip-cleanup
```

### Actualizar Imágenes
```bash
# Reconstruir imágenes
docker-compose build --no-cache

# Desplegar
./deploy.sh --skip-cleanup --skip-build
```

## 📝 Logs y Debugging

### Ubicación de Logs
- **Servidor Central**: `docker logs p2p-central-server`
- **Peer 1**: `docker logs p2p-peer-1`
- **Peer 2**: `docker logs p2p-peer-2`
- **Peer 3**: `docker logs p2p-peer-3`

### Niveles de Log
- **INFO**: Información general
- **WARNING**: Advertencias
- **ERROR**: Errores críticos
- **DEBUG**: Información detallada

### Debugging Avanzado
```bash
# Entrar al contenedor del servidor central
docker exec -it p2p-central-server bash

# Ver base de datos
docker exec -it p2p-central-server sqlite3 data/central_server.db

# Ver archivos del peer
docker exec -it p2p-peer-1 ls -la shared_files/
```

## 🚨 Troubleshooting Avanzado

### Problema: Puerto ocupado
```bash
# Encontrar proceso usando puerto 8000
netstat -ano | findstr :8000

# Terminar proceso (Windows)
taskkill /PID <PID> /F

# En Linux/macOS
lsof -ti:8000 | xargs kill -9
```

### Problema: Permisos de Docker
```bash
# Agregar usuario al grupo docker (Linux)
sudo usermod -aG docker $USER

# Reiniciar sesión
logout
```

### Problema: Memoria insuficiente
```bash
# Verificar uso de memoria
docker system df

# Limpiar sistema
docker system prune -a --volumes
```

## 📞 Soporte

Si encuentras problemas:

1. **Revisar logs** del servicio afectado
2. **Verificar prerrequisitos** (Docker, puertos)
3. **Consultar documentación** en `README.md`
4. **Ejecutar pruebas** con `scripts/test_web_interface.ps1`
5. **Crear issue** en el repositorio del proyecto

## 🎉 ¡Listo!

Una vez completado el despliegue, tendrás:

- ✅ **Servidor central** ejecutándose en http://localhost:8000
- ✅ **3 nodos peer** conectados y funcionando
- ✅ **Interfaz web** abierta en tu navegador
- ✅ **Sistema completo** listo para usar

¡Disfruta usando RedP2P! 🚀

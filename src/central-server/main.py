import asyncio
import uvicorn
import logging
import signal
import sys
from contextlib import asynccontextmanager

from api.rest_api import CentralServerAPI
from services.reconnection_manager import reconnection_manager
from services.backup_manager import backup_manager
from services.alert_manager import alert_manager
from services.business_metrics import business_metrics
from cache.redis_cache import redis_cache
from monitoring.resource_monitor import resource_monitor
from utils.advanced_logging import setup_advanced_logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CentralServer:
    """Servidor central de coordinación P2P"""
    
    def __init__(self):
        self.api = CentralServerAPI()
        self.app = self.api.get_app()
        self.running = False
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Inicia el servidor central"""
        try:
            self.running = True
            logger.info(f"Iniciando servidor central en {host}:{port}")
            
            # Inicializar servicios
            await self._initialize_services()
            
            # Configurar servidor
            config = uvicorn.Config(
                self.app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
            server = uvicorn.Server(config)
            
            # Ejecutar servidor
            await server.serve()
            
        except Exception as e:
            logger.error(f"Error iniciando servidor central: {e}")
            raise
    
    async def _initialize_services(self):
        """Inicializa los servicios del servidor"""
        try:
            # Configurar logging avanzado
            setup_advanced_logging()
            logger.info("Sistema de logging avanzado inicializado")
            
            # Inicializar Redis cache
            await redis_cache.connect()
            logger.info("Redis cache inicializado")
            
            # Inicializar gestor de reconexión
            await reconnection_manager.start()
            logger.info("Gestor de reconexión iniciado")
            
            # Inicializar gestor de backup
            await backup_manager.start()
            logger.info("Gestor de backup iniciado")
            
            # Inicializar gestor de alertas
            await alert_manager.start()
            logger.info("Gestor de alertas iniciado")
            
            # Inicializar métricas de negocio
            await business_metrics.start()
            logger.info("Recolector de métricas de negocio iniciado")
            
            # Inicializar monitor de recursos
            logger.info("Monitor de recursos inicializado")
            
        except Exception as e:
            logger.error(f"Error inicializando servicios: {e}")
            # Continuar sin los servicios opcionales
    
    async def stop(self):
        """Detiene el servidor central"""
        try:
            self.running = False
            
            # Detener servicios
            await business_metrics.stop()
            await alert_manager.stop()
            await backup_manager.stop()
            await reconnection_manager.stop()
            await redis_cache.disconnect()
            
            logger.info("Servidor central detenido")
        except Exception as e:
            logger.error(f"Error deteniendo servidor central: {e}")

# Instancia global del servidor
central_server = CentralServer()

def signal_handler(signum, frame):
    """Maneja señales del sistema"""
    logger.info(f"Recibida señal {signum}, deteniendo servidor...")
    asyncio.create_task(central_server.stop())
    sys.exit(0)

async def main():
    """Función principal"""
    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Obtener configuración desde variables de entorno
        host = "0.0.0.0"
        port = 8000
        
        # Iniciar servidor
        await central_server.start(host, port)
        
    except KeyboardInterrupt:
        logger.info("Interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error en main: {e}")
    finally:
        await central_server.stop()

if __name__ == "__main__":
    asyncio.run(main())

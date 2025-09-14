"""
Sistema de cache con Redis para mejorar performance
"""

import json
import asyncio
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisCache:
    """Cache con Redis para almacenar datos frecuentemente accedidos"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.redis_client: Optional[redis.Redis] = None
        self.connected = False
    
    async def connect(self):
        """Conecta al servidor Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            
            # Probar conexión
            await self.redis_client.ping()
            self.connected = True
            logger.info(f"Conectado a Redis en {self.host}:{self.port}")
            
        except Exception as e:
            logger.warning(f"No se pudo conectar a Redis: {e}")
            self.connected = False
    
    async def disconnect(self):
        """Desconecta del servidor Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            logger.info("Desconectado de Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del cache"""
        if not self.connected or not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo del cache {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Almacena un valor en el cache"""
        if not self.connected or not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl_seconds, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error almacenando en cache {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Elimina una clave del cache"""
        if not self.connected or not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error eliminando del cache {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Verifica si una clave existe en el cache"""
        if not self.connected or not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error verificando existencia de clave {key}: {e}")
            return False
    
    async def get_or_set(self, key: str, factory_func, ttl_seconds: int = 300) -> Any:
        """Obtiene del cache o ejecuta función y almacena resultado"""
        # Intentar obtener del cache
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Si no está en cache, ejecutar función
        try:
            if asyncio.iscoroutinefunction(factory_func):
                value = await factory_func()
            else:
                value = factory_func()
            
            # Almacenar en cache
            await self.set(key, value, ttl_seconds)
            return value
            
        except Exception as e:
            logger.error(f"Error en get_or_set para {key}: {e}")
            raise e
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalida todas las claves que coincidan con el patrón"""
        if not self.connected or not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error invalidando patrón {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        if not self.connected or not self.redis_client:
            return {"connected": False}
        
        try:
            info = await self.redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de Redis: {e}")
            return {"connected": False, "error": str(e)}

# Instancia global del cache
redis_cache = RedisCache()

# Funciones de conveniencia para cache de peers
async def cache_peer_info(peer_id: str, peer_info: Dict[str, Any], ttl: int = 300):
    """Cachea información de un peer"""
    key = f"peer_info:{peer_id}"
    await redis_cache.set(key, peer_info, ttl)

async def get_cached_peer_info(peer_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene información de peer del cache"""
    key = f"peer_info:{peer_id}"
    return await redis_cache.get(key)

async def invalidate_peer_cache(peer_id: str = None):
    """Invalida cache de peers"""
    if peer_id:
        await redis_cache.delete(f"peer_info:{peer_id}")
    else:
        await redis_cache.invalidate_pattern("peer_info:*")

# Funciones de conveniencia para cache de archivos
async def cache_file_search(query: str, results: list, ttl: int = 60):
    """Cachea resultados de búsqueda de archivos"""
    key = f"file_search:{hash(query)}"
    await redis_cache.set(key, results, ttl)

async def get_cached_file_search(query: str) -> Optional[list]:
    """Obtiene resultados de búsqueda del cache"""
    key = f"file_search:{hash(query)}"
    return await redis_cache.get(key)

async def invalidate_file_cache():
    """Invalida cache de archivos"""
    await redis_cache.invalidate_pattern("file_search:*")

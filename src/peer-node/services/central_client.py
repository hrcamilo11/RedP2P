import asyncio
import aiohttp
from typing import List, Optional, Dict
from datetime import datetime
from models.file_info import FileInfo, SearchRequest, SearchResponse, DownloadRequest, DownloadResponse, UploadRequest, UploadResponse
import logging

logger = logging.getLogger(__name__)

class CentralClient:
    """Cliente para comunicación con el servidor central"""
    
    def __init__(self, central_server_url: str, peer_id: str, peer_host: str, peer_port: int, peer_grpc_port: int):
        self.central_server_url = central_server_url
        self.peer_id = peer_id
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.peer_grpc_port = peer_grpc_port
        self.session: Optional[aiohttp.ClientSession] = None
        self.registered = False
    
    async def initialize(self):
        """Inicializa el cliente"""
        self.session = aiohttp.ClientSession()
        success = await self.register_with_central()
        if not success:
            logger.error(f"Failed to register peer {self.peer_id} with central server after all retries")
    
    async def close(self):
        """Cierra el cliente"""
        if self.session:
            await self.session.close()
    
    async def register_with_central(self) -> bool:
        """Registra el peer con el servidor central"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                registration_data = {
                    "peer_id": self.peer_id,
                    "host": "localhost",  # Usar localhost para que el servidor central pueda conectarse
                    "port": self.peer_port,
                    "grpc_port": self.peer_grpc_port
                }
                
                url = f"{self.central_server_url}/api/peers/register"
                async with self.session.post(url, json=registration_data, timeout=10) as response:
                    if response.status == 200:
                        self.registered = True
                        logger.info(f"Peer {self.peer_id} registrado con servidor central")
                        return True
                    else:
                        logger.warning(f"Error registrando peer: HTTP {response.status} (intento {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        return False
            
            except Exception as e:
                logger.warning(f"Error registrando peer con servidor central (intento {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return False
        
        return False
    
    async def unregister_from_central(self) -> bool:
        """Desregistra el peer del servidor central"""
        try:
            url = f"{self.central_server_url}/api/peers/{self.peer_id}"
            async with self.session.delete(url, timeout=10) as response:
                if response.status == 200:
                    self.registered = False
                    logger.info(f"Peer {self.peer_id} desregistrado del servidor central")
                    return True
                else:
                    logger.error(f"Error desregistrando peer: HTTP {response.status}")
                    return False
        
        except Exception as e:
            logger.error(f"Error desregistrando peer del servidor central: {e}")
            return False
    
    async def search_files_central(self, search_request: SearchRequest) -> SearchResponse:
        """Busca archivos a través del servidor central"""
        try:
            url = f"{self.central_server_url}/api/files/search"
            async with self.session.post(url, json=search_request.dict(), timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return SearchResponse(**data)
                else:
                    logger.error(f"Error buscando archivos: HTTP {response.status}")
                    return SearchResponse(files=[], total_found=0, search_time=0.0, searched_peers=[])
        
        except Exception as e:
            logger.error(f"Error buscando archivos en servidor central: {e}")
            return SearchResponse(files=[], total_found=0, search_time=0.0, searched_peers=[])
    
    async def download_file_central(self, download_request: DownloadRequest) -> DownloadResponse:
        """Inicia una descarga a través del servidor central"""
        try:
            url = f"{self.central_server_url}/api/transfers/download"
            async with self.session.post(url, json=download_request.dict(), timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return DownloadResponse(**data)
                else:
                    error_data = await response.json()
                    return DownloadResponse(
                        success=False,
                        error_message=error_data.get("detail", "Error desconocido")
                    )
        
        except Exception as e:
            logger.error(f"Error iniciando descarga en servidor central: {e}")
            return DownloadResponse(
                success=False,
                error_message=f"Error de conexión: {str(e)}"
            )
    
    async def upload_file_central(self, upload_request: UploadRequest) -> UploadResponse:
        """Inicia una subida a través del servidor central"""
        try:
            url = f"{self.central_server_url}/api/transfers/upload"
            async with self.session.post(url, json=upload_request.dict(), timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return UploadResponse(**data)
                else:
                    error_data = await response.json()
                    return UploadResponse(
                        success=False,
                        error_message=error_data.get("detail", "Error desconocido")
                    )
        
        except Exception as e:
            logger.error(f"Error iniciando subida en servidor central: {e}")
            return UploadResponse(
                success=False,
                error_message=f"Error de conexión: {str(e)}"
            )
    
    async def sync_files_with_central(self, files: List[FileInfo]) -> bool:
        """Sincroniza archivos locales con el servidor central"""
        try:
            # Primero indexar archivos en el servidor central
            url = f"{self.central_server_url}/api/files/index/{self.peer_id}"
            async with self.session.post(url, timeout=30) as response:
                if response.status == 200:
                    logger.info(f"Archivos del peer {self.peer_id} sincronizados con servidor central")
                    return True
                else:
                    logger.error(f"Error sincronizando archivos: HTTP {response.status}")
                    return False
        
        except Exception as e:
            logger.error(f"Error sincronizando archivos con servidor central: {e}")
            return False
    
    async def get_central_stats(self) -> Optional[Dict]:
        """Obtiene estadísticas del servidor central"""
        try:
            url = f"{self.central_server_url}/api/stats"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error obteniendo estadísticas: HTTP {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del servidor central: {e}")
            return None
    
    async def get_online_peers(self) -> List[Dict]:
        """Obtiene lista de peers en línea desde el servidor central"""
        try:
            url = f"{self.central_server_url}/api/peers/online"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error obteniendo peers en línea: HTTP {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error obteniendo peers en línea del servidor central: {e}")
            return []
    
    async def health_check_central(self) -> bool:
        """Verifica la salud del servidor central"""
        try:
            url = f"{self.central_server_url}/api/health"
            async with self.session.get(url, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.debug(f"Error verificando salud del servidor central: {e}")
            return False

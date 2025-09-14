import asyncio
import aiohttp
from typing import List, Optional, Dict
from models.file_info import FileInfo, SearchRequest, SearchResponse, DownloadRequest, DownloadResponse
from services.file_locator import FileLocator
from services.file_transfer import FileTransfer

class PClient:
    """Cliente P2P para comunicación entre peers"""
    
    def __init__(self, peer_id: str, file_locator: FileLocator, file_transfer: FileTransfer):
        self.peer_id = peer_id
        self.file_locator = file_locator
        self.file_transfer = file_transfer
        self.connected_peers: Dict[str, dict] = {}
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Inicializa el cliente"""
        self._session = aiohttp.ClientSession()
        await self.file_locator.initialize()
        await self.file_transfer.initialize()
    
    async def close(self):
        """Cierra el cliente"""
        if self._session:
            await self._session.close()
        await self.file_locator.close()
        await self.file_transfer.close()
    
    async def search_files(self, search_request: SearchRequest) -> SearchResponse:
        """Busca archivos en la red P2P"""
        return await self.file_locator.search_files(search_request)
    
    async def download_file(self, file_hash: str, peer_id: str) -> DownloadResponse:
        """Descarga un archivo desde un peer específico"""
        # Obtener información del peer
        peer_info = self.connected_peers.get(peer_id)
        if not peer_info:
            # Intentar descubrir el peer
            peer_info = await self._discover_peer(peer_id)
            if not peer_info:
                return DownloadResponse(
                    success=False,
                    error_message=f"Peer {peer_id} no encontrado"
                )
        
        download_request = DownloadRequest(file_hash=file_hash, peer_id=peer_id)
        return await self.file_transfer.download_file(
            download_request, 
            peer_info['host'], 
            peer_info['port']
        )
    
    async def upload_file(self, file_path: str, target_peer_id: str) -> bool:
        """Sube un archivo a un peer específico"""
        try:
            # Leer archivo
            async with aiofiles.open(file_path, 'rb') as f:
                file_data = await f.read()
            
            # Calcular hash
            import hashlib
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Obtener información del peer
            peer_info = self.connected_peers.get(target_peer_id)
            if not peer_info:
                peer_info = await self._discover_peer(target_peer_id)
                if not peer_info:
                    return False
            
            # Simular subida
            return await self.file_transfer.simulate_upload(
                file_hash, 
                peer_info['host'], 
                peer_info['port']
            )
        
        except Exception as e:
            print(f"Error subiendo archivo: {e}")
            return False
    
    async def _discover_peer(self, peer_id: str) -> Optional[dict]:
        """Descubre un peer en la red"""
        # En un sistema real, esto consultaría un servicio de descubrimiento
        # Por ahora, retornamos None si no está en peers conocidos
        return None
    
    async def ping_peer(self, peer_id: str) -> bool:
        """Hace ping a un peer para verificar conectividad"""
        peer_info = self.connected_peers.get(peer_id)
        if not peer_info:
            return False
        
        try:
            url = f"http://{peer_info['host']}:{peer_info['port']}/api/health"
            async with self._session.get(url, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def get_peer_status(self, peer_id: str) -> dict:
        """Obtiene el estado de un peer"""
        peer_info = self.connected_peers.get(peer_id)
        if not peer_info:
            return {"status": "unknown", "available": False}
        
        is_available = await self.ping_peer(peer_id)
        return {
            "status": "online" if is_available else "offline",
            "available": is_available,
            "host": peer_info['host'],
            "port": peer_info['port']
        }
    
    async def discover_network(self) -> List[str]:
        """Descubre peers en la red"""
        return await self.file_locator.discover_peers()
    
    async def sync_with_peer(self, peer_id: str) -> bool:
        """Sincroniza el índice local con un peer"""
        try:
            peer_info = self.connected_peers.get(peer_id)
            if not peer_info:
                return False
            
            url = f"http://{peer_info['host']}:{peer_info['port']}/api/sync"
            async with self._session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Procesar archivos del peer
                    for file_data in data.get('files', []):
                        file_info = FileInfo(**file_data)
                        await self.file_locator.file_indexer.add_file(file_info)
                    return True
                return False
        
        except Exception as e:
            print(f"Error sincronizando con peer {peer_id}: {e}")
            return False

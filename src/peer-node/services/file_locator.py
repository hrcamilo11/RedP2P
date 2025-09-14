import asyncio
import aiohttp
from typing import List, Optional, Dict
from models.file_info import FileInfo, SearchRequest, SearchResponse
from services.file_indexer import FileIndexer
import time

class FileLocator:
    """Servicio de localización de archivos en la red P2P"""
    
    def __init__(self, file_indexer: FileIndexer, network_config):
        self.file_indexer = file_indexer
        self.network_config = network_config
        self.known_peers: Dict[str, dict] = {}
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Inicializa el cliente HTTP"""
        self._session = aiohttp.ClientSession()
        
        # Añadir peers conocidos
        self.known_peers[self.network_config.primary_friend.peer_id] = {
            'host': self.network_config.primary_friend.host,
            'port': self.network_config.primary_friend.port,
            'is_available': True
        }
        self.known_peers[self.network_config.backup_friend.peer_id] = {
            'host': self.network_config.backup_friend.host,
            'port': self.network_config.backup_friend.port,
            'is_available': True
        }
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self._session:
            await self._session.close()
    
    async def search_files(self, search_request: SearchRequest) -> SearchResponse:
        """Busca archivos en toda la red P2P"""
        start_time = time.time()
        all_files = []
        
        # Buscar en el índice local primero
        local_files = await self.file_indexer.search_files(
            filename=search_request.filename,
            file_hash=search_request.file_hash,
            min_size=search_request.min_size,
            max_size=search_request.max_size
        )
        all_files.extend(local_files)
        
        # Buscar en peers remotos
        remote_files = await self._search_remote_peers(search_request)
        all_files.extend(remote_files)
        
        # Eliminar duplicados por hash
        unique_files = {}
        for file_info in all_files:
            unique_files[file_info.hash] = file_info
        
        search_time = time.time() - start_time
        
        return SearchResponse(
            files=list(unique_files.values()),
            total_found=len(unique_files),
            search_time=search_time
        )
    
    async def _search_remote_peers(self, search_request: SearchRequest) -> List[FileInfo]:
        """Busca archivos en peers remotos"""
        tasks = []
        
        for peer_id, peer_info in self.known_peers.items():
            if peer_info['is_available']:
                task = self._search_peer(peer_id, peer_info, search_request)
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados y manejar excepciones
            all_files = []
            for result in results:
                if isinstance(result, Exception):
                    print(f"Error en búsqueda remota: {result}")
                elif isinstance(result, list):
                    all_files.extend(result)
            
            return all_files
        
        return []
    
    async def _search_peer(self, peer_id: str, peer_info: dict, search_request: SearchRequest) -> List[FileInfo]:
        """Busca archivos en un peer específico"""
        try:
            url = f"http://{peer_info['host']}:{peer_info['port']}/api/search"
            
            params = {}
            if search_request.filename:
                params['filename'] = search_request.filename
            if search_request.file_hash:
                params['file_hash'] = search_request.file_hash
            if search_request.min_size:
                params['min_size'] = search_request.min_size
            if search_request.max_size:
                params['max_size'] = search_request.max_size
            
            async with self._session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    files = [FileInfo(**file_data) for file_data in data.get('files', [])]
                    return files
                else:
                    print(f"Error en peer {peer_id}: {response.status}")
                    return []
        
        except asyncio.TimeoutError:
            print(f"Timeout en peer {peer_id}")
            peer_info['is_available'] = False
            return []
        except Exception as e:
            print(f"Error conectando con peer {peer_id}: {e}")
            peer_info['is_available'] = False
            return []
    
    async def get_file_from_peer(self, file_hash: str, peer_id: str) -> Optional[FileInfo]:
        """Obtiene un archivo específico de un peer"""
        if peer_id in self.known_peers:
            peer_info = self.known_peers[peer_id]
            try:
                url = f"http://{peer_info['host']}:{peer_info['port']}/api/file/{file_hash}"
                
                async with self._session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return FileInfo(**data)
                    else:
                        print(f"Archivo no encontrado en peer {peer_id}")
                        return None
            
            except Exception as e:
                print(f"Error obteniendo archivo de peer {peer_id}: {e}")
                peer_info['is_available'] = False
                return None
        
        return None
    
    async def discover_peers(self) -> List[str]:
        """Descubre nuevos peers en la red"""
        discovered_peers = []
        
        for peer_id, peer_info in self.known_peers.items():
            if peer_info['is_available']:
                try:
                    url = f"http://{peer_info['host']}:{peer_info['port']}/api/peers"
                    
                    async with self._session.get(url, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            for new_peer in data.get('peers', []):
                                if new_peer['peer_id'] not in self.known_peers:
                                    self.known_peers[new_peer['peer_id']] = {
                                        'host': new_peer['host'],
                                        'port': new_peer['port'],
                                        'is_available': True
                                    }
                                    discovered_peers.append(new_peer['peer_id'])
                
                except Exception as e:
                    print(f"Error descubriendo peers desde {peer_id}: {e}")
                    peer_info['is_available'] = False
        
        return discovered_peers

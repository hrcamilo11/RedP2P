import os
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from models.file_info import FileInfo

class FileIndexer:
    """Servicio de indexación de archivos locales"""
    
    def __init__(self, shared_directory: str, peer_id: str):
        self.shared_directory = shared_directory
        self.peer_id = peer_id
        self.file_index: Dict[str, FileInfo] = {}
        self._lock = asyncio.Lock()
    
    async def scan_directory(self) -> List[FileInfo]:
        """Escanea el directorio compartido y actualiza el índice"""
        async with self._lock:
            files = []
            try:
                for root, dirs, filenames in os.walk(self.shared_directory):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        try:
                            file_info = FileInfo.from_file(file_path, self.peer_id)
                            files.append(file_info)
                            self.file_index[file_info.hash] = file_info
                        except Exception as e:
                            print(f"Error indexando archivo {file_path}: {e}")
                            continue
            except Exception as e:
                print(f"Error escaneando directorio {self.shared_directory}: {e}")
            
            return files
    
    async def get_file_by_hash(self, file_hash: str) -> Optional[FileInfo]:
        """Obtiene información de un archivo por su hash"""
        async with self._lock:
            return self.file_index.get(file_hash)
    
    async def search_files(self, filename: Optional[str] = None, 
                          file_hash: Optional[str] = None,
                          min_size: Optional[int] = None,
                          max_size: Optional[int] = None) -> List[FileInfo]:
        """Busca archivos en el índice local"""
        async with self._lock:
            results = []
            
            for file_info in self.file_index.values():
                # Filtro por nombre
                if filename and filename.lower() not in file_info.filename.lower():
                    continue
                
                # Filtro por hash
                if file_hash and file_info.hash != file_hash:
                    continue
                
                # Filtro por tamaño
                if min_size and file_info.size < min_size:
                    continue
                
                if max_size and file_info.size > max_size:
                    continue
                
                results.append(file_info)
            
            return results
    
    async def add_file(self, file_info: FileInfo) -> None:
        """Añade un archivo al índice"""
        async with self._lock:
            self.file_index[file_info.hash] = file_info
    
    async def remove_file(self, file_hash: str) -> bool:
        """Elimina un archivo del índice"""
        async with self._lock:
            if file_hash in self.file_index:
                del self.file_index[file_hash]
                return True
            return False
    
    async def get_all_files(self) -> List[FileInfo]:
        """Obtiene todos los archivos del índice"""
        async with self._lock:
            return list(self.file_index.values())
    
    async def update_file_availability(self, file_hash: str, is_available: bool) -> bool:
        """Actualiza la disponibilidad de un archivo"""
        async with self._lock:
            if file_hash in self.file_index:
                self.file_index[file_hash].is_available = is_available
                return True
            return False

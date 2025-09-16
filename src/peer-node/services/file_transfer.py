import asyncio
import aiohttp
import aiofiles
import os
from typing import Optional, AsyncGenerator, Dict
from models.file_info import FileInfo, DownloadRequest, DownloadResponse, UploadRequest, UploadResponse
from services.file_indexer import FileIndexer

class FileTransfer:
    """Servicio de transferencia de archivos entre peers"""
    
    def __init__(self, file_indexer: FileIndexer, shared_directory: str, peer_id: str, central_client: Optional[object] = None):
        self.file_indexer = file_indexer
        self.shared_directory = shared_directory
        self.peer_id = peer_id
        self.active_transfers: Dict[str, dict] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self.central_client = central_client

    def set_central_client(self, central_client: object) -> None:
        """Inyecta el cliente del servidor central después de la construcción."""
        self.central_client = central_client
    
    async def initialize(self):
        """Inicializa el cliente HTTP"""
        self._session = aiohttp.ClientSession()
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self._session:
            await self._session.close()
    
    async def download_file(self, download_request: DownloadRequest, 
                          target_peer_host: str, target_peer_port: int) -> DownloadResponse:
        """Descarga un archivo desde otro peer"""
        try:
            # Verificar si el archivo existe localmente
            local_file = await self.file_indexer.get_file_by_hash(download_request.file_hash)
            if local_file and local_file.is_available:
                return DownloadResponse(
                    success=True,
                    file_info=local_file,
                    download_url=f"http://localhost:8001/api/download/{download_request.file_hash}"
                )
            
            # Descargar desde el peer remoto
            url = f"http://{target_peer_host}:{target_peer_port}/api/download/{download_request.file_hash}"
            
            async with self._session.get(url, timeout=30) as response:
                if response.status == 200:
                    # Crear directorio si no existe
                    os.makedirs(self.shared_directory, exist_ok=True)
                    
                    # Obtener nombre del archivo del header
                    filename = response.headers.get('Content-Disposition', '').split('filename=')[-1]
                    if not filename:
                        filename = f"downloaded_{download_request.file_hash[:8]}"
                    
                    file_path = os.path.join(self.shared_directory, filename)
                    
                    # Descargar archivo
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    # Indexar el nuevo archivo
                    file_info = FileInfo.from_file(file_path, self.peer_id)
                    await self.file_indexer.add_file(file_info)

                    # Sincronizar con servidor central (mejora: reflectar descargas de inmediato)
                    try:
                        if self.central_client:
                            files = await self.file_indexer.get_all_files()
                            await self.central_client.sync_files_with_central(files)
                    except Exception:
                        # No bloquear por errores de sincronización
                        pass
                    
                    return DownloadResponse(
                        success=True,
                        file_info=file_info,
                        download_url=f"http://localhost:8001/api/download/{download_request.file_hash}"
                    )
                else:
                    return DownloadResponse(
                        success=False,
                        error_message=f"Error descargando archivo: {response.status}"
                    )
        
        except asyncio.TimeoutError:
            return DownloadResponse(
                success=False,
                error_message="Timeout descargando archivo"
            )
        except Exception as e:
            return DownloadResponse(
                success=False,
                error_message=f"Error descargando archivo: {str(e)}"
            )
    
    async def upload_file(self, upload_request: UploadRequest, 
                         file_data: bytes) -> UploadResponse:
        """Simula la subida de un archivo (en un sistema real, esto se enviaría a otro peer)"""
        try:
            # Crear directorio si no existe
            os.makedirs(self.shared_directory, exist_ok=True)
            
            # Crear archivo
            file_path = os.path.join(self.shared_directory, upload_request.filename)
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            
            # Verificar que el hash coincida
            import hashlib
            calculated_hash = hashlib.sha256(file_data).hexdigest()
            if calculated_hash != upload_request.file_hash:
                os.remove(file_path)
                return UploadResponse(
                    success=False,
                    error_message="Hash del archivo no coincide"
                )
            
            # Indexar el archivo
            file_info = FileInfo.from_file(file_path, self.peer_id)
            await self.file_indexer.add_file(file_info)

            # Sincronizar con servidor central (mejora: reflectar subidas de inmediato)
            try:
                if self.central_client:
                    files = await self.file_indexer.get_all_files()
                    await self.central_client.sync_files_with_central(files)
            except Exception:
                # No bloquear por errores de sincronización
                pass
            
            return UploadResponse(
                success=True,
                file_id=file_info.hash
            )
        
        except Exception as e:
            return UploadResponse(
                success=False,
                error_message=f"Error subiendo archivo: {str(e)}"
            )
    
    async def get_file_stream(self, file_hash: str) -> Optional[AsyncGenerator[bytes, None]]:
        """Obtiene un stream del archivo para descarga"""
        file_info = await self.file_indexer.get_file_by_hash(file_hash)
        if not file_info or not file_info.is_available:
            return
        
        try:
            async with aiofiles.open(file_info.path, 'rb') as f:
                while True:
                    chunk = await f.read(8192)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            print(f"Error leyendo archivo {file_hash}: {e}")
            return
    
    async def simulate_download(self, file_hash: str, target_peer_host: str, 
                              target_peer_port: int) -> bool:
        """Simula una descarga (para pruebas)"""
        try:
            # Simular tiempo de descarga
            await asyncio.sleep(1)
            
            # Simular verificación de disponibilidad
            url = f"http://{target_peer_host}:{target_peer_port}/api/file/{file_hash}"
            async with self._session.get(url, timeout=5) as response:
                return response.status == 200
        
        except Exception as e:
            print(f"Error en simulación de descarga: {e}")
            return False
    
    async def simulate_upload(self, file_hash: str, target_peer_host: str, 
                            target_peer_port: int) -> bool:
        """Simula una subida (para pruebas)"""
        try:
            # Simular tiempo de subida
            await asyncio.sleep(1)
            
            # Simular verificación de recepción
            url = f"http://{target_peer_host}:{target_peer_port}/api/upload"
            data = {"file_hash": file_hash, "status": "received"}
            async with self._session.post(url, json=data, timeout=5) as response:
                return response.status == 200
        
        except Exception as e:
            print(f"Error en simulación de subida: {e}")
            return False

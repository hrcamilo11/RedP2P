from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional
import asyncio
import os
from models.file_info import FileInfo, SearchRequest, SearchResponse, DownloadRequest, DownloadResponse, UploadRequest, UploadResponse
from services.file_indexer import FileIndexer
from services.file_locator import FileLocator
from services.file_transfer import FileTransfer
from services.pclient import PClient
from services.central_client import CentralClient

class RESTAPI:
    """API REST para el peer"""
    
    def __init__(self, peer_id: str, config, file_indexer: FileIndexer, 
                 file_locator: FileLocator, file_transfer: FileTransfer, pclient: PClient, central_client: CentralClient):
        self.peer_id = peer_id
        self.config = config
        self.file_indexer = file_indexer
        self.file_locator = file_locator
        self.file_transfer = file_transfer
        self.pclient = pclient
        self.central_client = central_client
        self.app = FastAPI(title=f"P2P Peer {peer_id}", version="1.0.0")
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API"""
        
        @self.app.get("/api/health")
        async def health_check():
            """Verificación de salud del peer"""
            return {
                "status": "healthy",
                "peer_id": self.peer_id,
                "files_count": len(await self.file_indexer.get_all_files())
            }
        
        @self.app.get("/api/files")
        async def get_all_files():
            """Obtiene todos los archivos del peer"""
            files = await self.file_indexer.get_all_files()
            return {"files": [file.dict() for file in files]}
        
        @self.app.get("/api/file/{file_hash}")
        async def get_file_info(file_hash: str):
            """Obtiene información de un archivo específico"""
            file_info = await self.file_indexer.get_file_by_hash(file_hash)
            if not file_info:
                raise HTTPException(status_code=404, detail="Archivo no encontrado")
            return file_info.dict()
        
        @self.app.get("/api/download/{file_hash}")
        async def download_file(file_hash: str):
            """Descarga un archivo"""
            file_info = await self.file_indexer.get_file_by_hash(file_hash)
            if not file_info or not file_info.is_available:
                raise HTTPException(status_code=404, detail="Archivo no encontrado o no disponible")
            
            if not os.path.exists(file_info.path):
                raise HTTPException(status_code=404, detail="Archivo no existe en el sistema de archivos")
            
            def file_generator():
                with open(file_info.path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk
            
            return StreamingResponse(
                file_generator(),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={file_info.filename}",
                    "Content-Length": str(file_info.size)
                }
            )
        
        @self.app.post("/api/search")
        async def search_files(search_request: SearchRequest):
            """Busca archivos en la red P2P (local + central)"""
            try:
                # Buscar localmente primero
                local_response = await self.file_locator.search_files(search_request)
                
                # Buscar en servidor central
                central_response = await self.central_client.search_files_central(search_request)
                
                # Combinar resultados
                all_files = local_response.files + central_response.files
                
                # Eliminar duplicados por hash
                unique_files = {}
                for file_info in all_files:
                    unique_files[file_info.hash] = file_info
                
                combined_response = SearchResponse(
                    files=list(unique_files.values()),
                    total_found=len(unique_files),
                    search_time=local_response.search_time + central_response.search_time,
                    searched_peers=local_response.searched_peers + central_response.searched_peers
                )
                
                return combined_response.dict()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            """Sube un archivo al peer"""
            try:
                import os
                import hashlib
                
                # Crear directorio si no existe
                os.makedirs(self.file_transfer.shared_directory, exist_ok=True)
                
                # Leer contenido del archivo
                content = await file.read()
                
                # Calcular hash
                file_hash = hashlib.sha256(content).hexdigest()
                
                # Guardar archivo
                file_path = os.path.join(self.file_transfer.shared_directory, file.filename)
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "message": "Archivo subido correctamente",
                    "filename": file.filename,
                    "file_hash": file_hash,
                    "size": len(content)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/files/{file_hash}")
        async def delete_file(file_hash: str):
            """Elimina un archivo del peer"""
            try:
                # Buscar el archivo en el directorio compartido
                import os
                import glob
                
                files = glob.glob(os.path.join(self.file_transfer.shared_directory, "*"))
                for file_path in files:
                    if os.path.isfile(file_path):
                        # Calcular hash del archivo
                        import hashlib
                        with open(file_path, 'rb') as f:
                            file_hash_calculated = hashlib.sha256(f.read()).hexdigest()
                        
                        if file_hash_calculated == file_hash:
                            os.remove(file_path)
                            return {"success": True, "message": "Archivo eliminado correctamente"}
                
                raise HTTPException(status_code=404, detail="Archivo no encontrado")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/peers")
        async def get_known_peers():
            """Obtiene la lista de peers conocidos"""
            peers = []
            for peer_id, peer_info in self.file_locator.known_peers.items():
                peers.append({
                    "peer_id": peer_id,
                    "host": peer_info['host'],
                    "port": peer_info['port'],
                    "available": peer_info['is_available']
                })
            return {"peers": peers}
        
        @self.app.post("/api/sync")
        async def sync_files():
            """Sincroniza archivos con otros peers"""
            try:
                # Escanear directorio local
                files = await self.file_indexer.scan_directory()
                return {"files": [file.dict() for file in files]}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/download-request")
        async def download_request(download_request: DownloadRequest):
            """Procesa una solicitud de descarga"""
            try:
                # Obtener información del archivo
                file_info = await self.file_indexer.get_file_by_hash(download_request.file_hash)
                if not file_info:
                    return DownloadResponse(
                        success=False,
                        error_message="Archivo no encontrado"
                    ).dict()
                
                return DownloadResponse(
                    success=True,
                    file_info=file_info,
                    download_url=f"/api/download/{download_request.file_hash}"
                ).dict()
            except Exception as e:
                return DownloadResponse(
                    success=False,
                    error_message=str(e)
                ).dict()
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Obtiene estadísticas del peer"""
            files = await self.file_indexer.get_all_files()
            total_size = sum(file.size for file in files)
            
            return {
                "peer_id": self.peer_id,
                "total_files": len(files),
                "total_size": total_size,
                "available_files": len([f for f in files if f.is_available]),
                "known_peers": len(self.file_locator.known_peers)
            }
    
    def get_app(self):
        """Retorna la aplicación FastAPI"""
        return self.app

import grpc
from concurrent import futures
import asyncio
from typing import List
from models.file_info import FileInfo, SearchRequest, SearchResponse, DownloadRequest, DownloadResponse
from services.file_indexer import FileIndexer
from services.file_locator import FileLocator
from services.file_transfer import FileTransfer

# Importar los archivos generados por protobuf (se crearán después)
# from proto import p2p_pb2, p2p_pb2_grpc

class P2PService:
    """Servicio gRPC para comunicación P2P"""
    
    def __init__(self, peer_id: str, file_indexer: FileIndexer, 
                 file_locator: FileLocator, file_transfer: FileTransfer):
        self.peer_id = peer_id
        self.file_indexer = file_indexer
        self.file_locator = file_locator
        self.file_transfer = file_transfer
    
    async def SearchFiles(self, request, context):
        """Implementa la búsqueda de archivos vía gRPC"""
        try:
            search_request = SearchRequest(
                filename=request.filename if hasattr(request, 'filename') else None,
                file_hash=request.file_hash if hasattr(request, 'file_hash') else None,
                min_size=request.min_size if hasattr(request, 'min_size') else None,
                max_size=request.max_size if hasattr(request, 'max_size') else None
            )
            
            response = await self.file_locator.search_files(search_request)
            
            # Convertir respuesta a formato gRPC
            # return p2p_pb2.SearchResponse(
            #     files=[self._file_info_to_grpc(file) for file in response.files],
            #     total_found=response.total_found,
            #     search_time=response.search_time
            # )
            
            # Por ahora, retornamos un diccionario (se implementará con protobuf)
            return {
                "files": [file.dict() for file in response.files],
                "total_found": response.total_found,
                "search_time": response.search_time
            }
        
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None
    
    async def GetFileInfo(self, request, context):
        """Obtiene información de un archivo específico"""
        try:
            file_hash = request.file_hash if hasattr(request, 'file_hash') else request
            file_info = await self.file_indexer.get_file_by_hash(file_hash)
            
            if not file_info:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Archivo no encontrado")
                return None
            
            # return self._file_info_to_grpc(file_info)
            return file_info.dict()
        
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None
    
    async def DownloadFile(self, request, context):
        """Procesa una solicitud de descarga"""
        try:
            file_hash = request.file_hash if hasattr(request, 'file_hash') else request
            peer_id = request.peer_id if hasattr(request, 'peer_id') else self.peer_id
            
            download_request = DownloadRequest(file_hash=file_hash, peer_id=peer_id)
            
            # Obtener información del archivo
            file_info = await self.file_indexer.get_file_by_hash(file_hash)
            if not file_info:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Archivo no encontrado")
                return None
            
            # return p2p_pb2.DownloadResponse(
            #     success=True,
            #     file_info=self._file_info_to_grpc(file_info),
            #     download_url=f"http://localhost:8001/api/download/{file_hash}"
            # )
            
            return {
                "success": True,
                "file_info": file_info.dict(),
                "download_url": f"http://localhost:8001/api/download/{file_hash}"
            }
        
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None
    
    async def GetPeerStatus(self, request, context):
        """Obtiene el estado del peer"""
        try:
            files = await self.file_indexer.get_all_files()
            total_size = sum(file.size for file in files)
            
            # return p2p_pb2.PeerStatus(
            #     peer_id=self.peer_id,
            #     status="online",
            #     total_files=len(files),
            #     total_size=total_size,
            #     available_files=len([f for f in files if f.is_available])
            # )
            
            return {
                "peer_id": self.peer_id,
                "status": "online",
                "total_files": len(files),
                "total_size": total_size,
                "available_files": len([f for f in files if f.is_available])
            }
        
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None
    
    def _file_info_to_grpc(self, file_info: FileInfo):
        """Convierte FileInfo a formato gRPC"""
        # return p2p_pb2.FileInfo(
        #     filename=file_info.filename,
        #     size=file_info.size,
        #     hash=file_info.hash,
        #     peer_id=file_info.peer_id,
        #     last_modified=file_info.last_modified.isoformat(),
        #     path=file_info.path,
        #     is_available=file_info.is_available
        # )
        return file_info.dict()

class GRPCServer:
    """Servidor gRPC para el peer"""
    
    def __init__(self, peer_id: str, port: int, file_indexer: FileIndexer, 
                 file_locator: FileLocator, file_transfer: FileTransfer):
        self.peer_id = peer_id
        self.port = port
        self.file_indexer = file_indexer
        self.file_locator = file_locator
        self.file_transfer = file_transfer
        self.server = None
    
    async def start(self):
        """Inicia el servidor gRPC"""
        self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        
        # Crear instancia del servicio
        service = P2PService(
            self.peer_id, 
            self.file_indexer, 
            self.file_locator, 
            self.file_transfer
        )
        
        # Registrar el servicio (se implementará con protobuf)
        # p2p_pb2_grpc.add_P2PServiceServicer_to_server(service, self.server)
        
        listen_addr = f'[::]:{self.port}'
        self.server.add_insecure_port(listen_addr)
        
        await self.server.start()
        print(f"Servidor gRPC iniciado en puerto {self.port}")
    
    async def stop(self):
        """Detiene el servidor gRPC"""
        if self.server:
            await self.server.stop(grace=5)
            print("Servidor gRPC detenido")

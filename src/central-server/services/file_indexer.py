import asyncio
import aiohttp
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.database import File, Peer, get_db
from models.schemas import FileInfo, SearchRequest, SearchResponse
from services.peer_manager import PeerManager
from config.hosts import map_host
import logging

logger = logging.getLogger(__name__)

class CentralFileIndexer:
    """Indexador central de archivos de todos los peers"""
    
    def __init__(self, peer_manager: PeerManager):
        self.peer_manager = peer_manager
        self.session = aiohttp.ClientSession()
        self._lock = asyncio.Lock()
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self.session:
            await self.session.close()
    
    async def index_peer_files(self, peer_id: str, db: Session) -> bool:
        """Indexa archivos de un peer específico"""
        try:
            # Obtener información del peer
            peer = db.query(Peer).filter(Peer.peer_id == peer_id).first()
            if not peer or not peer.is_online:
                logger.warning(f"Peer {peer_id} no está disponible para indexación")
                return False
            
            # Obtener archivos del peer
            # Mapear localhost a nombres de contenedores Docker
            mapped_host = map_host(peer.host, peer.port)
            url = f"http://{mapped_host}/api/files"
            logger.info(f"Intentando indexar archivos del peer {peer_id} desde {url}")
            try:
                # Usar aiohttp para consistencia con el resto del sistema
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as response:
                        if response.status != 200:
                            logger.error(f"Error obteniendo archivos del peer {peer_id}: HTTP {response.status}")
                            return False
                        
                        data = await response.json()
                        files_data = data.get('files', [])
                        
                        # NO eliminar archivos subidos - solo marcar como no disponibles los que no están en el directorio local
                        # Los archivos subidos se mantienen en la BD para preservar la funcionalidad
                        existing_files = db.query(File).filter(File.peer_id == peer_id).all()
                        local_file_hashes = set()
                        
                        # Indexar nuevos archivos y actualizar existentes
                        indexed_count = 0
                        for file_data in files_data:
                            try:
                                file_hash = file_data['hash']
                                local_file_hashes.add(file_hash)
                                
                                # Buscar si el archivo ya existe
                                existing_file = db.query(File).filter(
                                    File.file_hash == file_hash,
                                    File.peer_id == peer_id
                                ).first()
                                
                                if existing_file:
                                    # Actualizar archivo existente - solo si no es un archivo subido
                                    if existing_file.source != 'upload':
                                        existing_file.filename = file_data['filename']
                                        existing_file.size = file_data['size']
                                        existing_file.is_available = file_data.get('is_available', True)
                                        existing_file.last_modified = datetime.fromisoformat(file_data['last_modified'].replace('Z', '+00:00'))
                                        existing_file.updated_at = datetime.utcnow()
                                        logger.debug(f"Archivo {file_data['filename']} actualizado en peer {peer_id}")
                                    else:
                                        logger.debug(f"Archivo {file_data['filename']} es un archivo subido, no se actualiza")
                                else:
                                    # Crear nuevo archivo indexado
                                    file_record = File(
                                        filename=file_data['filename'],
                                        file_hash=file_data['hash'],
                                        size=file_data['size'],
                                        peer_id=peer_id,
                                        is_available=file_data.get('is_available', True),
                                        source='indexed',  # Marcar como archivo indexado
                                        last_modified=datetime.fromisoformat(file_data['last_modified'].replace('Z', '+00:00')),
                                        created_at=datetime.utcnow()
                                    )
                                    db.add(file_record)
                                    logger.debug(f"Archivo {file_data['filename']} indexado en peer {peer_id}")
                                
                                indexed_count += 1
                            except Exception as e:
                                logger.error(f"Error indexando archivo {file_data.get('filename', 'unknown')}: {e}")
                                continue
                        
                        # Marcar como no disponibles los archivos que no están en el directorio local
                        # Incluye también archivos subidos (source='upload') si ya no existen localmente
                        for existing_file in existing_files:
                            if existing_file.file_hash not in local_file_hashes:
                                existing_file.is_available = False
                                existing_file.updated_at = datetime.utcnow()
                                logger.debug(f"Archivo {existing_file.filename} marcado como no disponible (no en directorio local)")
                        
                        db.commit()
                        logger.info(f"Indexados {indexed_count} archivos del peer {peer_id}")
                        
            except Exception as e:
                logger.error(f"Error conectando con peer {peer_id}: {e}")
                return False
            return True
            
        except Exception as e:
            logger.error(f"Error indexando archivos del peer {peer_id}: {e}")
            db.rollback()
            return False
    
    async def index_all_peers(self, db: Session) -> Dict[str, bool]:
        """Indexa archivos de todos los peers en línea"""
        try:
            online_peers = await self.peer_manager.get_online_peers(db)
            results = {}
            
            # Indexar cada peer concurrentemente
            tasks = []
            for peer_info in online_peers:
                task = self._index_peer_async(peer_info.peer_id, db)
                tasks.append((peer_info.peer_id, task))
            
            # Ejecutar todas las tareas
            for peer_id, task in tasks:
                try:
                    result = await task
                    results[peer_id] = result
                except Exception as e:
                    logger.error(f"Error en indexación concurrente del peer {peer_id}: {e}")
                    results[peer_id] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error indexando todos los peers: {e}")
            return {}
    
    async def _index_peer_async(self, peer_id: str, db: Session) -> bool:
        """Indexa un peer de forma asíncrona"""
        return await self.index_peer_files(peer_id, db)
    
    async def search_files(self, search_request: SearchRequest, db: Session) -> SearchResponse:
        """Busca archivos en el índice central"""
        try:
            start_time = datetime.utcnow()
            
            # Construir consulta
            query = db.query(File).join(Peer)
            
            # Aplicar filtros
            if search_request.filename:
                query = query.filter(File.filename.contains(search_request.filename))
            
            if search_request.file_hash:
                query = query.filter(File.file_hash == search_request.file_hash)
            
            if search_request.min_size:
                query = query.filter(File.size >= search_request.min_size)
            
            if search_request.max_size:
                query = query.filter(File.size <= search_request.max_size)
            
            if search_request.peer_id:
                query = query.filter(File.peer_id == search_request.peer_id)
            
            # Solo archivos disponibles
            query = query.filter(File.is_available == True)
            
            # Ejecutar consulta
            files = query.all()
            
            # Convertir a FileInfo
            file_infos = []
            for file in files:
                file_info = FileInfo(
                    id=file.id,
                    filename=file.filename,
                    file_hash=file.file_hash,
                    size=file.size,
                    peer_id=file.peer_id,
                    is_available=file.is_available,
                    last_modified=file.last_modified
                )
                file_infos.append(file_info)
            
            # Calcular tiempo de búsqueda
            search_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Obtener peers que se consultaron
            searched_peers = list(set([f.peer_id for f in files]))
            
            return SearchResponse(
                files=file_infos,
                total_found=len(file_infos),
                search_time=search_time,
                searched_peers=searched_peers
            )
            
        except Exception as e:
            logger.error(f"Error buscando archivos: {e}")
            return SearchResponse(
                files=[],
                total_found=0,
                search_time=0.0,
                searched_peers=[]
            )
    
    async def get_file_info(self, file_hash: str, db: Session) -> Optional[FileInfo]:
        """Obtiene información de un archivo específico"""
        try:
            file = db.query(File).filter(File.file_hash == file_hash).first()
            if not file:
                return None
            
            return FileInfo(
                id=file.id,
                filename=file.filename,
                file_hash=file.file_hash,
                size=file.size,
                peer_id=file.peer_id,
                is_available=file.is_available,
                last_modified=file.last_modified
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo información del archivo {file_hash}: {e}")
            return None
    
    async def update_file_availability(self, file_hash: str, is_available: bool, db: Session) -> bool:
        """Actualiza la disponibilidad de un archivo"""
        try:
            file = db.query(File).filter(File.file_hash == file_hash).first()
            if file:
                file.is_available = is_available
                file.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error actualizando disponibilidad del archivo {file_hash}: {e}")
            db.rollback()
            return False
    
    async def get_peer_files(self, peer_id: str, db: Session, page: int = 1, limit: int = 50) -> List[FileInfo]:
        """Obtiene todos los archivos de un peer específico con paginación"""
        try:
            # Calcular offset
            offset = (page - 1) * limit
            
            # Obtener archivos con paginación
            files = db.query(File).filter(
                File.peer_id == peer_id,
                File.is_available == True
            ).offset(offset).limit(limit).all()
            file_infos = []
            
            for file in files:
                file_info = FileInfo(
                    id=file.id,
                    filename=file.filename,
                    file_hash=file.file_hash,
                    size=file.size,
                    peer_id=file.peer_id,
                    is_available=file.is_available,
                    last_modified=file.last_modified
                )
                file_infos.append(file_info)
            
            return file_infos
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos del peer {peer_id}: {e}")
            return []
    
    async def get_system_stats(self, db: Session) -> Dict[str, int]:
        """Obtiene estadísticas del sistema"""
        try:
            total_peers = db.query(Peer).count()
            online_peers = db.query(Peer).filter(Peer.is_online == True).count()
            total_files = db.query(File).count()
            available_files = db.query(File).filter(File.is_available == True).count()
            
            # Calcular tamaño total
            total_size = db.query(File).with_entities(
                func.sum(File.size)
            ).filter(File.is_available == True).scalar() or 0
            
            return {
                "total_peers": total_peers,
                "online_peers": online_peers,
                "total_files": total_files,
                "total_size": total_size,
                "active_transfers": 0,  # TODO: Implementar tracking de transferencias
                "completed_transfers_today": 0  # TODO: Implementar tracking de transferencias
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del sistema: {e}")
            return {
                "total_peers": 0,
                "online_peers": 0,
                "total_files": 0,
                "total_size": 0,
                "active_transfers": 0,
                "completed_transfers_today": 0
            }
